#!/usr/bin/env python3
"""Deterministic review signals for plain Korean prose. Not a quality grader."""
import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

CONNECTIVES = ['그리고', '그러나', '그런데', '하지만', '그래서', '따라서', '또한', '반면', '즉', '그러므로', '그렇지만', '게다가', '한편']
CANDIDATES = ['리듬', '매듭', '켜켜이', '여정', '무엇인가', '본질', '가치']

def sentences(text):
    result = []
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text.strip()) if p.strip()]
    for p_id, paragraph in enumerate(paragraphs, 1):
        prose = re.sub(r'\s+', ' ', paragraph).strip()
        for match in re.finditer(r'.+?(?:[.!?。！？]+[”’"\']*(?=\s|$)|$)', prose):
            value = match.group().strip()
            if value:
                result.append((p_id, value))
    return result

def validate_config(config):
    if not isinstance(config, dict):
        raise ValueError('점검 설정은 watch·preserve 목록을 가진 JSON 객체여야 합니다.')
    for field in ['watch', 'preserve']:
        values = config.get(field, [])
        if not isinstance(values, list) or any(not isinstance(v, str) or not v.strip() for v in values):
            raise ValueError(f'{field}에는 비어 있지 않은 문자열 목록을 적어주세요.')
    return config


def analyze(text, config=None):
    config = validate_config(config) if config is not None else None
    candidates = list(dict.fromkeys(config.get('watch', []))) if config is not None else CANDIDATES
    preserve = list(dict.fromkeys(config.get('preserve', []))) if config is not None else []
    rows = []
    terms = defaultdict(list)
    starts = Counter()
    connectives = []
    for index, (paragraph, sentence) in enumerate(sentences(text), 1):
        tokens = re.findall(r'\S+', sentence)
        row = {'id': index, 'paragraph': paragraph, 'text': sentence, 'chars_with_spaces': len(sentence), 'chars_without_spaces': len(re.sub(r'\s', '', sentence)), 'eojeol': len(tokens)}
        lead = re.match(r'^[“‘"\']*(' + '|'.join(CONNECTIVES) + r')(?=[\s,，]|$)', sentence)
        row['leading_connective'] = lead.group(1) if lead else None
        if lead:
            connectives.append({'sentence': index, 'expression': lead.group(1)})
        row['expression_candidates'] = [term for term in candidates if term in sentence]
        row['preserve_candidates'] = [term for term in preserve if term in sentence]
        for token in re.findall(r'[가-힣A-Za-z0-9]+', sentence):
            terms[token].append(index)
        starts[tokens[0] if tokens else ''] += 1
        rows.append(row)
    lengths = [row['chars_with_spaces'] for row in rows]
    return {
        'schema_version': 1,
        'input_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
        'definitions': {'chars': 'Unicode code points; no readability threshold', 'eojeol': 'whitespace-separated units, not English words or morphemes', 'connectives': 'listed sentence-initial expressions only; not all Korean connective endings', 'boundaries': 'paragraph and punctuation heuristic; check abbreviations and quotations manually', 'repetition': 'exact surface tokens; morphology not normalized', 'policy': 'signals_only_no_quality_score'},
        'summary': {'sentences': len(rows), 'paragraphs': len(set(r['paragraph'] for r in rows)), 'mean_chars_with_spaces': round(sum(lengths)/len(lengths), 1) if lengths else 0, 'max_chars_with_spaces': max(lengths, default=0), 'leading_connectives': len(connectives), 'expression_candidates': sum(len(r['expression_candidates']) for r in rows)},
        'longest_sentences': [r['id'] for r in sorted(rows, key=lambda r: (-r['chars_with_spaces'], r['id']))[:3]],
        'connectives': connectives,
        'repeated_surface_tokens': [{'token': token, 'count': len(locations), 'sentences': locations} for token, locations in sorted(terms.items(), key=lambda item: (-len(item[1]), item[0])) if len(locations) >= 3],
        'sentences': rows,
        'custom_checks': config,
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--config', type=Path, help='개인 점검어 watch·보존 참고어 preserve JSON')
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding='utf-8')) if args.config else None
        report = analyze(args.input.read_text(encoding='utf-8'), config)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    s = report['summary']
    print(f"문장 {s['sentences']}개 | 평균 {s['mean_chars_with_spaces']}자 | 최대 {s['max_chars_with_spaces']}자 | 문장 앞 연결 표현 {s['leading_connectives']}개")
    print('글자 수: 공백 포함. 수치 감소는 품질 향상을 뜻하지 않습니다.')
    print(f'JSON: {args.output}')

if __name__ == '__main__':
    main()
