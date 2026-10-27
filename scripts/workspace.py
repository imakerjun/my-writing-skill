#!/usr/bin/env python3
"""한 문단의 판단을 개인 지침과 설치 가능한 글쓰기 스킬로 잇는다. LLM 호출 없음."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.3.1'


def now():
    return datetime.now(timezone.utc).isoformat()


def slug(value):
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', value) or len(value) > 64:
        raise ValueError('이름은 64자 이내의 영문 소문자·숫자·하이픈으로 적어주세요.')
    return value


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def load_profile(workspace):
    data = json.loads((workspace / 'profile.json').read_text(encoding='utf-8'))
    slug(data['name'])
    if data.get('schema_version') != 1 or not isinstance(data.get('rules'), list):
        raise ValueError('지원하는 profile.json 형식이 아닙니다.')
    return data


def initialize(args):
    name = slug(args.name)
    if name == 'my-writing-skill':
        raise ValueError('공통 스킬과 구분할 개인 이름을 골라주세요. 예: my-voice')
    workspace = args.workspace
    workspace.mkdir(parents=True, exist_ok=False)
    save(workspace / 'profile.json', {'schema_version': 1, 'name': name, 'rules': []})
    save(workspace / 'checks.json', {'watch': [], 'preserve': []})
    shutil.copyfile(ROOT / 'templates/brief.md', workspace / 'brief.md')
    (workspace / 'ratings.jsonl').write_text('', encoding='utf-8')
    print(f'준비됨: {workspace}\nbrief.md에 독자와 전할 뜻을 적고, 초안 한 문단으로 시작하세요.')


def propose(args):
    profile = load_profile(args.workspace)
    records = (args.workspace / 'ratings.jsonl').read_text(encoding='utf-8').splitlines()
    if args.rating < 1 or args.rating > len(records):
        raise ValueError('ratings.jsonl에서 실제로 받은 평가의 줄 번호를 지정하세요.')
    rating = json.loads(records[args.rating - 1])
    if rating.get('source') != 'author_supplied' or type(rating.get('score')) is not int or rating['score'] not in [0, 1, 2]:
        raise ValueError('실제 저자에게 받은 정수 평가만 지침의 근거로 연결합니다.')
    if not rating.get('reason_verbatim', '').strip() or not rating.get('evidence', '').strip():
        raise ValueError('이유와 근거 구절이 있는 평가가 필요합니다.')
    for field in ['instruction', 'question', 'scope']:
        if not getattr(args, field).strip():
            raise ValueError(f'{field}를 비워둘 수 없습니다.')
    rule_id = 'r' + str(len(profile['rules']) + 1).zfill(3)
    profile['rules'].append({
        'id': rule_id, 'status': 'proposed', 'instruction': args.instruction,
        'scope': args.scope, 'exceptions': args.exception, 'eval_question': args.question,
        'rating_line': args.rating, 'rating': rating, 'proposed_at': now()
    })
    save(args.workspace / 'profile.json', profile)
    print(f'{rule_id}: 지침 후보를 기록했습니다. 저자의 확인 전에는 개인 스킬에 포함하지 않습니다.')


def confirm(args):
    profile = load_profile(args.workspace)
    rule = next((r for r in profile['rules'] if r['id'] == args.rule), None)
    if rule is None:
        raise ValueError('해당 지침이 없습니다.')
    rule['status'] = 'confirmed'
    rule['confirmed_at'] = now()
    save(args.workspace / 'profile.json', profile)
    print(f'{args.rule}: 확인한 지침으로 기록했습니다. 다음에는 다른 문단에서 확인하세요.')


def eval_case(args):
    profile = load_profile(args.workspace)
    name = slug(args.name)
    if not args.fix and not args.preserve:
        raise ValueError('고칠 표현 또는 남길 표현을 하나 이상 지정하세요.')
    text = args.input.read_text(encoding='utf-8')
    for span in args.fix + args.preserve:
        if not span.strip() or span not in text:
            raise ValueError(f'입력에 없는 구절입니다: {span!r}')
    if any(a in b or b in a for a in args.fix for b in args.preserve):
        raise ValueError('고칠 표현과 보존할 표현이 겹칩니다. 기대 결과를 문맥에 맞게 다시 나눠주세요.')
    destination = args.workspace / 'eval/cases' / name
    destination.mkdir(parents=True, exist_ok=False)
    (destination / 'input.md').write_text(text, encoding='utf-8')
    expected = {
        'case': name, 'source': 'user-specified exact spans; local development case',
        'planted': [{'id': f'p{i}', 'match': span, 'span': span, 'type': '개인 점검 표현'} for i, span in enumerate(args.fix, 1)],
        'traps': [{'id': f't{i}', 'match': span, 'span': span, 'reason': '이 문맥에서 남길 표현'} for i, span in enumerate(args.preserve, 1)],
        'thresholds': {'recall_min': 1.0 if args.fix else None, 'max_trap_fp': 0},
        'judge_items': [r['eval_question'] for r in profile['rules'] if r['status'] == 'confirmed']
    }
    if args.tone:
        expected['tone'] = args.tone
    save(destination / 'expected.json', expected)
    print(f'생성됨: {destination}\n모델에는 input.md만 주고, expected.json은 숨긴 뒤 응답을 채점하세요.')


def build(args):
    profile = load_profile(args.workspace)
    confirmed = [r for r in profile['rules'] if r.get('status') == 'confirmed']
    if not confirmed:
        raise ValueError('확인된 지침이 없습니다. 저자의 점수와 이유를 받고 지침을 확인한 뒤 만드세요.')
    name = profile['name']
    destination = args.output or args.workspace / 'skill' / name
    if destination.exists():
        raise ValueError('출력 폴더가 이미 있습니다. 다른 출력 경로를 써서 기존 스킬을 보존하세요.')
    checks = json.loads((args.workspace / 'checks.json').read_text(encoding='utf-8'))
    # Validate before creating any output.
    sys.path.insert(0, str(ROOT / 'scripts'))
    from analyze import validate_config
    validate_config(checks)
    destination.mkdir(parents=True)
    for folder in ['scripts', 'references', 'agents', 'eval', 'templates']:
        (destination / folder).mkdir()
    for file in ['analyze.py', 'record_rating.py', 'grade.py']:
        shutil.copyfile(ROOT / 'scripts' / file, destination / 'scripts' / file)
    for file in ['signals.md', 'review-signals.md', 'reader-review.md']:
        shutil.copyfile(ROOT / 'references' / file, destination / 'references' / file)
    conversation = (ROOT / 'references/first-session.md').read_text(encoding='utf-8')
    conversation = conversation.replace('자세한 명령은 [기록 안내](feedback-loop.md)를 읽는다.',
                                        '실제 정수 점수와 이유는 이 스킬의 `scripts/record_rating.py`로 기록한다.')
    (destination / 'references/first-session.md').write_text(conversation, encoding='utf-8')
    shutil.copyfile(ROOT / 'eval/judge-rubric.md', destination / 'eval/judge-rubric.md')
    shutil.copyfile(ROOT / 'install.py', destination / 'install.py')
    shutil.copyfile(ROOT / 'LICENSE', destination / 'LICENSE')
    shutil.copyfile(ROOT / 'templates/reader-profile.json', destination / 'templates/reader-profile.json')
    shutil.copyfile(args.workspace / 'brief.md', destination / 'references/brief.md')
    save(destination / 'checks.json', checks)
    save(destination / 'references/author-profile.json', {**profile, 'rules': confirmed})
    save(destination / 'eval/criteria.json', {'questions': [{'scope': r['scope'], 'question': r['eval_question'], 'rule_id': r['id']} for r in confirmed], 'status': 'author-confirmed criteria; new-passage verification still required'})
    cases = args.workspace / 'eval/cases'
    if cases.exists():
        shutil.copytree(cases, destination / 'eval/cases')
    rules = '\n'.join(f"- **{r['id']} · {r['scope']}**: {r['instruction']}" + (f" 예외: {' / '.join(r['exceptions'])}" if r['exceptions'] else '') for r in confirmed)
    skill = f'''---
name: {name}
description: 이 저자의 한국어 초안을 확인된 문체 지침에 맞춰 다듬고, 저자의 점수와 이유로 기준을 갱신한다. 저자 문체로 쓰기·퇴고 요청에 사용한다.
metadata:
  version: "1"
---

# {name} · 내 글쓰기 스킬

이 스킬은 저자가 확인한 {len(confirmed)}개 지침으로 시작한다. 코드가 자꾸 고치는 표현을 찾고, LLM이 앞뒤를 읽으며 고친다. 저자는 내 글에 쓰고 싶은지 읽고 판단한다.

## 대화할 때

먼저 [첫 대화와 피드백 말투](references/first-session.md)를 읽는다. 편한 존댓말로 이야기하되, 고친 원고의 말투는 사용자 요청을 따른다. 목적이 이미 보이면 소개나 설문 대신 후보 한 문단부터 보여준다. 필요한 질문 하나만 하고, 칭찬을 반복하기보다 사용자가 짚은 구절을 어떻게 고칠지 말한다. 점수의 뜻은 처음에만 짧게 안내하고 사용자의 답을 기다린다.

## 이번 글부터 확인한다

사용자가 준 초안과 독자·전할 뜻을 먼저 읽는다. [장별 브리프](references/brief.md)는 이전 맥락이므로 이번 글과 다르면 이번 요청을 우선한다. 말로 풀어 쓴 메모도 초안 재료로 받는다. 핵심이 불분명할 때만 질문 하나를 하고 기다린다.

## 저자가 확인한 기준

{rules}

이유 원문·근거 구절·적용 범위·예외는 [개인 기준](references/author-profile.json)에 있다. 한 번의 판단을 모든 글의 금지어로 확대하지 않는다.

## 세 가지 협업

1. **코드 × LLM**: 이 스킬 폴더의 `scripts/analyze.py 원문.txt --config checks.json --output 관찰값.json`으로 위치를 찾고, LLM이 문맥을 보고 수정·보존·보류한다. 숫자를 줄이는 것을 목표로 삼지 않는다. [측정 범위](references/signals.md)와 [점검 후보](references/review-signals.md)는 필요할 때 읽는다.
2. **나 × LLM**: 독자에게 전할 뜻과 다음 행동을 살려 후보 하나를 보여준다. 사실·화자·말투를 보존하고, 없는 경험·대사·성과를 만들지 않는다. 다음 후보를 만들기 전에 저자의 0=이건 아니다 / 1=애매함 / 2=좋다와 이유를 기다린다. 점수나 채택을 대신 정하지 않는다. 이유에서 새 지침을 제안하되 저자 확인 전에는 확정하지 않는다.
3. **독자 역할 × 편집 역할**: 요청받으면 [독자 리뷰](references/reader-review.md) 절차로 읽힌다. 저자가 반영할 리뷰를 고른 뒤 그 부분을 수정하고 다시 리뷰한다. 합성 반응을 실제 사람의 반응으로 부르지 않는다.

평가는 `scripts/record_rating.py`로 실제 저자의 답만 기록한다. 근사·조건부 점수는 정수로 바꾸지 않는다. [다른 문단에서 볼 질문](eval/criteria.json)으로 다시 확인한다. eval/cases가 있으면 입력만으로 모델 응답을 받고 `scripts/grade.py 사례폴더 응답.md`로 고칠 말·남길 말의 문자열 검사를 한다. 기대 결과는 실행 모델에게 주지 않는다. 코드 통과와 뜻·자연스러움·실제 채택은 따로 확인한다.

이는 지침과 맥락을 갱신하는 방법이며 모델 가중치를 학습시킨 결과가 아니다. 한 번에 후보 하나와 중요한 수정 이유부터 보여주고, 전체 변경 표는 필요할 때 제공한다. 원고를 직접 수정해달라는 요청이 없으면 별도 후보로 보여준다.
'''
    (destination / 'SKILL.md').write_text(skill, encoding='utf-8')
    (destination / 'agents/openai.yaml').write_text('interface:\n  display_name: ' + json.dumps(name + ' · 내 글쓰기', ensure_ascii=False) + '\n  short_description: "내가 확인한 이유와 문장으로 글을 다듬는 개인 스킬"\n  default_prompt: ' + json.dumps(f'${name}로 내 초안 한 문단을 다듬어줘. 후보 하나를 보고 내가 점수와 이유를 남길게.', ensure_ascii=False) + '\n', encoding='utf-8')
    save(destination / 'build.json', {'builder_version': VERSION, 'built_at': now(), 'name': name, 'confirmed_rule_ids': [r['id'] for r in confirmed], 'model_fine_tuning': False, 'human_ratings_count': len({(r['rating_line'], r['rating']['candidate_sha256']) for r in confirmed}), 'new_passage_validation': 'pending'})
    print(f'개인 스킬 생성됨: {destination}\n설치: python3 {destination / "install.py"} codex\n개인 글·평가가 들어 있으므로 공개 저장소에 자동으로 올리지 않습니다.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('init', help='개인 작업 폴더 만들기'); p.add_argument('workspace', type=Path); p.add_argument('--name', default='my-voice'); p.set_defaults(action=initialize)
    p = sub.add_parser('propose', help='실제 평가에서 지침 후보와 eval 질문 기록'); p.add_argument('workspace', type=Path); p.add_argument('--rating', type=int, required=True); p.add_argument('--instruction', required=True); p.add_argument('--scope', required=True); p.add_argument('--question', required=True); p.add_argument('--exception', action='append', default=[]); p.set_defaults(action=propose)
    p = sub.add_parser('confirm', help='저자가 확인한 지침만 확정'); p.add_argument('workspace', type=Path); p.add_argument('--rule', required=True); p.set_defaults(action=confirm)
    p = sub.add_parser('eval-case', help='내 글의 고칠 표현·남길 표현을 기대 결과로 저장'); p.add_argument('workspace', type=Path); p.add_argument('--input', type=Path, required=True); p.add_argument('--name', required=True); p.add_argument('--fix', action='append', default=[]); p.add_argument('--preserve', action='append', default=[]); p.add_argument('--tone'); p.set_defaults(action=eval_case)
    p = sub.add_parser('build', help='확인된 기준으로 설치 가능한 개인 스킬 생성'); p.add_argument('workspace', type=Path); p.add_argument('--output', type=Path); p.set_defaults(action=build)
    args = parser.parse_args()
    try:
        args.action(args)
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as error:
        parser.exit(2, str(error) + '\n')


if __name__ == '__main__':
    main()
