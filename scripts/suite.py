#!/usr/bin/env python3
"""표현 점검·핵심 다듬기·독자 리뷰 스킬 세 개를 만든다. 모델 호출·자동 다운로드 없음."""
import argparse
import json
from pathlib import Path
import shutil
import tempfile

from analyze import validate_config
from expression_preferences import initialize as init_expressions
from personas import validate_profiles
from workspace import initialize as init_core, load_profile, save, slug

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.4.0'
MODES = {'expressions': 'AI 냄새 표현 점검', 'core': '핵심 다듬기', 'readers': '독자 리뷰'}


def initialize(path, name):
    slug(name)
    for mode in MODES:
        slug(name + '-' + mode)
    if path.exists():
        raise ValueError('이미 있는 작업 폴더입니다. 새 경로를 골라주세요.')
    path.mkdir(parents=True)
    save(path / 'creator.json', {'version': VERSION, 'name': name})
    init_expressions(path / 'expressions')
    init_core(argparse.Namespace(workspace=path / 'core', name=name + '-core'))
    save(path / 'readers/profiles.json', {'source_kind': 'not_selected', 'readers': []})
    (path / 'readers/reading-purpose.md').write_text('누가, 왜 이 글을 읽을까요? 이미 아는 것과 궁금해할 것을 적어주세요.\n', encoding='utf-8')
    print('세 스킬을 만들 준비가 됐어요. 기본 설정으로 먼저 만들거나, 예문과 문단에 점수·이유를 남겨보세요.')


def validate(workspace):
    creator = json.loads((workspace / 'creator.json').read_text(encoding='utf-8'))
    name = slug(creator['name'])
    for mode in MODES:
        slug(name + '-' + mode)
    checks = validate_config(json.loads((workspace / 'expressions/checks.json').read_text(encoding='utf-8')))
    for rating in checks.get('calibrations', []):
        if rating.get('source') != 'author_supplied' or type(rating.get('score')) is not int or rating['score'] not in (0, 1, 2):
            raise ValueError('표현 설정에는 실제 저자에게 받은 점수만 넣어주세요.')
        if not rating.get('scope') or not rating.get('reason_verbatim') or not rating.get('evidence') or rating['evidence'] not in rating.get('example', ''):
            raise ValueError('표현 점수의 예문·근거·범위·이유를 확인해주세요.')
    core = load_profile(workspace / 'core')
    confirmed = [r for r in core['rules'] if r.get('status') == 'confirmed']
    for rule in confirmed:
        rating = rule.get('rating', {})
        if rating.get('source') != 'author_supplied' or type(rating.get('score')) is not int or rating['score'] not in (0, 1, 2):
            raise ValueError('핵심 지침에는 실제 저자의 점수와 이유가 필요해요.')
        if any(not rule.get(key) for key in ['instruction', 'scope', 'eval_question']) or not rating.get('reason_verbatim'):
            raise ValueError('핵심 지침의 범위·질문·이유를 확인해주세요.')
    profiles = json.loads((workspace / 'readers/profiles.json').read_text(encoding='utf-8'))
    if profiles.get('readers'):
        validate_profiles(profiles)
    return name, checks, core, confirmed, profiles


def copy_resources(destination, mode):
    for folder in ['scripts', 'references', 'agents', 'templates', 'eval']:
        (destination / folder).mkdir(parents=True)
    for file in ['install.py', 'LICENSE']:
        shutil.copyfile(ROOT / file, destination / file)
    scripts = {'expressions': ['analyze.py', 'expression_preferences.py'],
               'core': ['record_rating.py', 'grade.py'], 'readers': ['personas.py', 'record_rating.py']}[mode]
    for file in scripts:
        shutil.copyfile(ROOT / 'scripts' / file, destination / 'scripts' / file)
    conversation = (ROOT / 'references/first-session.md').read_text(encoding='utf-8')
    conversation = conversation.replace('자세한 명령은 [기록 안내](feedback-loop.md)를 읽는다.',
                                        '실제 점수와 이유만 개인 작업 폴더에 기록한다.')
    (destination / 'references/first-session.md').write_text(conversation, encoding='utf-8')
    references = {'expressions': ['signals.md', 'review-signals.md'], 'core': [],
                  'readers': ['reader-workshop.md', 'persona-respondent.md']}[mode]
    for file in references:
        shutil.copyfile(ROOT / 'references' / file, destination / 'references' / file)
    if mode == 'expressions':
        shutil.copyfile(ROOT / 'templates/expression-examples.json', destination / 'templates/expression-examples.json')
    if mode == 'core':
        shutil.copyfile(ROOT / 'eval/judge-rubric.md', destination / 'eval/judge-rubric.md')


def build(workspace, output=None):
    name, checks, core, confirmed, profiles = validate(workspace)
    destination = output or workspace / 'skills'
    if destination.exists():
        raise ValueError('출력 폴더가 이미 있어요. --output으로 새 경로를 지정해주세요.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.writing-skills-', dir=destination.parent))
    entries = []
    try:
        for mode, label in MODES.items():
            skill_name = name + '-' + mode
            target = staging / skill_name
            copy_resources(target, mode)
            personal = '기본 설정으로 시작합니다. 아직 이 사용자가 확인한 개인 판단은 없습니다.'
            if mode == 'expressions':
                save(target / 'checks.json', checks)
                if checks.get('calibrations'):
                    personal = '예문에 준 점수와 이유는 checks.json의 calibrations에 있습니다. 예문의 맥락을 함께 읽습니다.'
            elif mode == 'core':
                shutil.copyfile(workspace / 'core/brief.md', target / 'references/brief.md')
                save(target / 'references/author-profile.json', {**core, 'rules': confirmed})
                save(target / 'eval/criteria.json', {'questions': [r['eval_question'] for r in confirmed], 'new_passage_validation': 'pending'})
                if confirmed:
                    personal = '\n'.join('- ' + r['instruction'] + ' (적용: ' + r['scope'] + '; 예외: ' + ', '.join(r.get('exceptions', [])) + ')' for r in confirmed)
                if (workspace / 'core/eval/cases').exists():
                    shutil.copytree(workspace / 'core/eval/cases', target / 'eval/cases')
            else:
                save(target / 'references/selected-readers.json', profiles)
                shutil.copyfile(workspace / 'readers/reading-purpose.md', target / 'references/reading-purpose.md')
                personal = ('선택한 실제 행과 출처는 references/selected-readers.json, 읽는 목적은 references/reading-purpose.md에 있습니다.'
                            if profiles.get('readers') else '아직 독자를 고르지 않았습니다. 데이터 준비와 독자 선정부터 도와줍니다. 데이터셋은 패키지에 포함하지 않습니다.')
            template = (ROOT / 'skill-templates' / (mode + '.md')).read_text(encoding='utf-8')
            (target / 'SKILL.md').write_text(template.replace('{{name}}', skill_name).replace('{{personal_notes}}', personal), encoding='utf-8')
            descriptions = {'expressions': '자꾸 고치는 표현을 코드로 찾고 앞뒤를 읽으며 고쳐봐요',
                            'core': '글에서 꼭 전할 말을 문단 하나에 담고 점수와 이유로 고쳐요',
                            'readers': '실제 합성 독자를 고르고 요약과 질문으로 원고를 다시 읽어요'}
            defaults = {'expressions': '이 문단에서 자꾸 고치는 표현을 찾아줘.', 'core': '이 문단에서 내가 전할 말을 같이 찾아보자.',
                        'readers': '이 글을 읽을 합성 독자를 고르고 리뷰를 받아보자.'}
            metadata = 'interface:\n  display_name: ' + json.dumps(label, ensure_ascii=False)
            metadata += '\n  short_description: ' + json.dumps(descriptions[mode], ensure_ascii=False)
            metadata += '\n  default_prompt: ' + json.dumps('$' + skill_name + ' ' + defaults[mode], ensure_ascii=False) + '\n'
            (target / 'agents/openai.yaml').write_text(metadata, encoding='utf-8')
            (target / 'README.md').write_text('# ' + label + '\n\n설치: `python3 install.py codex` 또는 `python3 install.py claude`\n\n새 대화에서 `$' + skill_name + '` 또는 `/' + skill_name + '`로 불러주세요. 개인 원고와 평가가 포함될 수 있으니 공유 전에 살펴봐주세요.\n', encoding='utf-8')
            save(target / 'build.json', {'builder_version': VERSION, 'mode': mode, 'name': skill_name,
                                        'confirmed_core_rules': len(confirmed) if mode == 'core' else 0,
                                        'expression_ratings': len(checks.get('calibrations', [])) if mode == 'expressions' else 0,
                                        'selected_readers': len(profiles.get('readers', [])) if mode == 'readers' else 0,
                                        'human_validation': 'not implied by generation', 'model_fine_tuning': False})
            entries.append({'name': skill_name, 'mode': mode, 'label': label})
        save(staging / 'suite.json', {'creator_version': VERSION, 'skills': entries})
        (staging / 'install.py').write_text('''#!/usr/bin/env python3
import argparse, json, subprocess, sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('target',choices=['codex','claude']);p.add_argument('--home',type=Path);p.add_argument('--uninstall',action='store_true');a=p.parse_args()
root=Path(__file__).resolve().parent
for skill in json.loads((root/'suite.json').read_text())['skills']:
    command=[sys.executable,str(root/skill['name']/'install.py'),a.target]
    if a.home:command+=['--home',str(a.home)]
    if a.uninstall:command+=['--uninstall']
    result=subprocess.run(command)
    if result.returncode:sys.exit(result.returncode)
''', encoding='utf-8')
        if destination.exists():
            raise ValueError('출력 경로가 생겼어요. 기존 폴더를 덮어쓰지 않습니다.')
        staging.rename(destination)
    except Exception:
        shutil.rmtree(staging)
        raise
    print(f'세 스킬을 만들었어요: {destination}\n설치: python3 {destination / "install.py"} codex')
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('init'); p.add_argument('workspace', type=Path); p.add_argument('--name', default='my-writing')
    p = sub.add_parser('build'); p.add_argument('workspace', type=Path); p.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        initialize(args.workspace, args.name) if args.command == 'init' else build(args.workspace, args.output)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, str(error) + '\n')


if __name__ == '__main__':
    main()
