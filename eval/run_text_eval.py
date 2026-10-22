#!/usr/bin/env python3
"""공개 예문을 정답 파일과 분리해 Claude CLI로 실행하고 나중에 채점한다."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--case', help='예: 03-causality; 생략하면 기존 세 사례')
    args = parser.parse_args()
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output = args.output_dir or ROOT/'local/eval-run'/stamp
    output.mkdir(parents=True, exist_ok=False)
    command = ['claude', '-p', '--safe-mode', '--tools', '', '--strict-mcp-config',
               '--no-session-persistence', '--output-format', 'json']
    skill = (ROOT/'SKILL.md').read_text()
    reference = (ROOT/'references/review-signals.md').read_text()
    measurement = (ROOT/'references/signals.md').read_text()
    manifest = {'started_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
                'skill_sha256':digest((ROOT/'SKILL.md').read_bytes()),
                'grader_sha256':digest((ROOT/'scripts/grade.py').read_bytes()),
                'command':command, 'withheld':['expected.json','grade.py','program-fixtures/'],
                'author_evaluation':None, 'cases':[]}
    cases = [ROOT/'eval/cases'/args.case] if args.case else sorted((ROOT/'eval/cases').iterdir())
    with tempfile.TemporaryDirectory(prefix='saramnaemsae-blind-') as isolated:
        for case in cases:
            original = (case/'input.md').read_text()
            prompt = ('이 실행에서는 도구가 제공되지 않습니다. 스킬의 선택사항인 코드 분석은 생략하고, '
                      '제공된 텍스트만으로 퇴고하세요. 파일을 찾거나 도구 호출/XML을 출력하지 마세요. '
                      '다음 공개 스킬을 적용해 마지막의 한국어 업무 기록을 퇴고해 주세요. 독자는 팀 동료입니다. '
                      '원래 뜻과 사실, 문체를 유지하고 후보는 하나만 제시하세요. 원문 파일은 수정하지 않습니다. '
                      '출력은 ## 수정본, ## 변경 기록 순서로 하세요. 변경이 없다면 스킬에서 정한 빈 표와 '
                      '적용/보류 0건을 적으세요. 저자의 미감 점수는 대신 매기지 마세요.\n\n<skill>\n'
                      + skill + '\n</skill>\n<review-signals>\n' + reference
                      + '\n</review-signals>\n<measurement-reference>\n' + measurement
                      + '\n</measurement-reference>\n<input>\n' + original + '\n</input>')
            (output/(case.name+'.prompt.txt')).write_text(prompt)
            result = subprocess.run(command,input=prompt,cwd=isolated,text=True,capture_output=True,timeout=240)
            (output/(case.name+'.raw.json')).write_text(result.stdout)
            (output/(case.name+'.stderr.txt')).write_text(result.stderr)
            entry = {'case':case.name, 'process_exit_code':result.returncode,
                     'prompt_sha256':digest(prompt.encode()), 'grade_exit_code':None}
            try:
                raw = json.loads(result.stdout)
                response = raw.get('result','')
                if result.returncode or raw.get('is_error') or not response.strip():
                    raise ValueError('모델 실행 실패. 자동채점을 건너뜁니다.')
                (output/(case.name+'.md')).write_text(response)
                entry['model_usage'] = raw.get('modelUsage',{})
                entry['response_sha256'] = digest(response.encode())
                grade = subprocess.run(['python3',str(ROOT/'scripts/grade.py'),str(case),str(output/(case.name+'.md'))],text=True,capture_output=True)
                (output/(case.name+'.grade.txt')).write_text(grade.stdout+grade.stderr)
                entry['grade_exit_code'] = grade.returncode
            except (ValueError, json.JSONDecodeError) as error:
                entry['error'] = str(error)
            manifest['cases'].append(entry)
            (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
            print(json.dumps(entry,ensure_ascii=False),flush=True)
    manifest['completed_at_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    return int(any(c.get('error') or c['grade_exit_code'] != 0 for c in manifest['cases']))


if __name__ == '__main__':
    raise SystemExit(main())
