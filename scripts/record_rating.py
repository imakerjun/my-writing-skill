#!/usr/bin/env python3
"""저자가 실제로 말한 0·1·2점과 이유를 JSONL에 기록한다."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('candidate', type=Path)
    p.add_argument('--score', type=int, choices=[0,1,2], required=True)
    p.add_argument('--reason', required=True)
    p.add_argument('--evidence', required=True, help='판단의 근거가 된 후보 속 구절')
    p.add_argument('--output', type=Path, required=True)
    a=p.parse_args()
    if not a.reason.strip() or not a.evidence.strip():p.error('이유와 근거 구절을 비워둘 수 없습니다.')
    data=a.candidate.read_bytes();text=data.decode('utf-8')
    if a.evidence not in text:p.error('근거 구절이 후보에 없습니다. 실제 구절을 그대로 적어주세요.')
    row={'at':datetime.now(timezone.utc).isoformat(),'candidate':str(a.candidate),'candidate_sha256':hashlib.sha256(data).hexdigest(),'score':a.score,'reason_verbatim':a.reason,'evidence':a.evidence,'source':'author_supplied','adopted':None}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('a',encoding='utf-8') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    print('저자의 점수와 이유를 기록했습니다. 실제 채택 여부는 별도로 확인합니다.')


if __name__=='__main__':main()
