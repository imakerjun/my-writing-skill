#!/usr/bin/env python3
"""예문에 준 실제 점수와 이유를 점검어 설정으로 남긴다. 자동 삭제는 하지 않는다."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def initialize(workspace, base_config=None):
    if workspace.exists():
        raise ValueError('이미 있는 폴더입니다. 새 경로를 골라주세요.')
    examples = json.loads((ROOT / 'templates/expression-examples.json').read_text(encoding='utf-8'))
    base = json.loads(base_config.read_text(encoding='utf-8')) if base_config else {'watch': examples['watch'], 'preserve': []}
    from analyze import validate_config
    validate_config(base)
    inherited = base.get('calibrations', [])
    if not isinstance(inherited, list) or any(item.get('source') != 'author_supplied' for item in inherited):
        raise ValueError('가져올 표현 판단의 출처를 확인해주세요.')
    workspace.mkdir(parents=True)
    write_json(workspace / 'base-checks.json', base)
    write_json(workspace / 'checks.json', {**base, 'calibrations': inherited, 'meaning': 'starter signals; not automatic deletion or AI detection'})
    (workspace / 'ratings.jsonl').write_text(''.join(json.dumps(item, ensure_ascii=False) + '\n' for item in inherited), encoding='utf-8')
    write_json(workspace / 'examples.json', examples)


def record(workspace, candidate, term, score, reason, evidence, scope):
    if type(score) is not int or score not in (0, 1, 2):
        raise ValueError('점수는 0·1·2 중 하나로 적어주세요.')
    if any(not value.strip() for value in (term, reason, evidence, scope)):
        raise ValueError('표현·이유·근거 구절·어떤 글인지 함께 적어주세요.')
    raw = candidate.read_bytes()
    text = raw.decode('utf-8')
    if evidence not in text or term not in evidence:
        raise ValueError('근거 구절은 예문에 있어야 하고 점검할 표현을 포함해야 합니다.')
    base = json.loads((workspace / 'base-checks.json').read_text(encoding='utf-8'))
    history_path = workspace / 'ratings.jsonl'
    history = [json.loads(line) for line in history_path.read_text(encoding='utf-8').splitlines() if line.strip()]
    row = {'source': 'author_supplied', 'at': datetime.now(timezone.utc).isoformat(),
           'term': term, 'score': score, 'scope': scope, 'reason_verbatim': reason,
           'evidence': evidence, 'example': text, 'candidate_sha256': hashlib.sha256(raw).hexdigest(),
           'decision': {0: 'review', 1: 'pending', 2: 'preserve_in_context'}[score]}
    history.append(row)
    latest = {(item['term'], item['scope']): item for item in history}
    watch = list(dict.fromkeys(base.get('watch', []) + [r['term'] for r in latest.values() if r['score'] == 0]))
    preserve = list(dict.fromkeys(base.get('preserve', []) + [r['term'] for r in latest.values() if r['score'] == 2]))
    write_json(workspace / 'checks.json', {'watch': watch, 'preserve': preserve,
               'calibrations': list(latest.values()), 'meaning': 'signals only; ratings belong to examples and scopes'})
    with history_path.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(row, ensure_ascii=False) + '\n')
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('init'); p.add_argument('workspace', type=Path); p.add_argument('--base-config', type=Path)
    p = sub.add_parser('rate'); p.add_argument('workspace', type=Path)
    p.add_argument('--candidate', type=Path, required=True); p.add_argument('--term', required=True)
    p.add_argument('--score', type=int, choices=[0, 1, 2], required=True); p.add_argument('--reason', required=True)
    p.add_argument('--evidence', required=True); p.add_argument('--scope', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'init':
            initialize(args.workspace, args.base_config)
            print('기본 점검어를 준비했어요. 예문 하나를 읽고 점수와 이유를 남겨주세요.')
        else:
            row = record(args.workspace, args.candidate, args.term, args.score, args.reason, args.evidence, args.scope)
            print({'review': '다시 읽을 표현으로 남겼어요.', 'pending': '판단을 보류했어요.',
                   'preserve_in_context': '이 문맥에서 유지할 표현으로 남겼어요.'}[row['decision']])
    except (OSError, ValueError, KeyError) as error:
        parser.exit(2, str(error) + '\n')


if __name__ == '__main__':
    main()
