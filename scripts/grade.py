#!/usr/bin/env python3
"""사람냄새 eval 채점기 — 결정적으로 잴 수 있는 것만 잰다.

사용법: python3 grade.py <case_dir> <result_file>

두 모드를 자동 판별한다.
- apply 모드(결과에 '## 수정본' 절이 있으면): 수정본에서 planted 부재(=고침)와
  trap 원문 존재(=보존)를 문자열로 검사한다 — trap 부재는 즉시 FAIL.
- propose 모드(그 외): 검토표에 planted 등장(=잡음)과 trap 등장(사람 확인)을 검사한다.

규율(전면 재작성·보관 원자료의 무단 수정·보류 분류)·after 품질은 judge-rubric.md로 사람/LLM이 판정한다.
현행 작업 파일의 수정은 기본 동작이며, 새 버전이나 별도 기록 파일의 생성 여부는 이 코드의 채점 대상이 아니다.
"""
import json
import re
import sys
from pathlib import Path


def normalize(text: str) -> str:
    text = re.sub(r"\*\*|__", "", text)  # 인용문 속 굵게 마커가 매칭을 깨지 않게
    return re.sub(r"\s+", " ", text)


def split_section(result: str, title: str) -> tuple[str | None, str]:
    """제목 섹션을 위치 기반으로 분리해 (섹션 본문, 나머지 전체)를 반환한다.
    문자열 replace에 기대면 주석 제거·공백 차이로 조용히 실패해 rest가 전체가 된다."""
    lines = result.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(rf"^#{{1,4}}\s*{title}", line.strip()):
            start = i
            break
    if start is None:
        return None, result
    end = start + 1
    while end < len(lines) and not re.match(r"^#{1,3}\s", lines[end]):
        end += 1
    section = "\n".join(lines[start + 1 : end])
    rest = "\n".join(lines[:start] + lines[end:])
    return section, rest


def extract_section(result: str, title: str) -> str | None:
    return split_section(result, title)[0]


def table_rows(text: str) -> list[list[str]]:
    """마크다운 표의 본문 행들을 셀 리스트로 반환(헤더·구분선 제외)."""
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue  # 구분선
        rows.append(cells)
    return rows[1:] if rows else []  # 첫 행은 헤더로 간주


def after_column(text: str) -> list[str]:
    lines = [l.strip() for l in text.splitlines() if l.strip().startswith("|")]
    if not lines:
        return []
    header = [c.strip().lower() for c in lines[0].strip("|").split("|")]
    idx = next((i for i, h in enumerate(header) if "after" in h or "제안" in h or "수정" in h), None)
    if idx is None:
        return []
    return [r[idx] for r in table_rows(text) if len(r) > idx]


POLITE = re.compile(r"(습니다|합니다|세요|네요|거든요|지요|어요|아요|죠)\s*[.!?'\"』」]*\s*$")


def polite_sentences(chunks: list[str]) -> list[str]:
    hits = []
    for chunk in chunks:
        # 따옴표 안(보존 인용)은 문체 판정에서 제외
        stripped = re.sub(r"[\"“'‘][^\"”'’]*[\"”'’]", "", chunk)
        for sent in re.split(r"(?<=[.!?])\s+", stripped):
            if sent and POLITE.search(sent.strip()):
                hits.append(sent.strip())
    return hits


def main() -> int:
    case_dir, result_file = Path(sys.argv[1]), Path(sys.argv[2])
    exp = json.loads((case_dir / "expected.json").read_text(encoding="utf-8"))
    result_raw = result_file.read_text(encoding="utf-8")

    failures = []
    revised, rest_raw = split_section(result_raw, "수정본")
    mode = "apply" if revised is not None else "propose"
    print(f"=== {exp['case']} — {result_file.name} [{mode} 모드] ===")

    planted = exp.get("planted", [])
    traps = exp.get("traps", [])
    thresholds = exp.get("thresholds", {})

    if mode == "apply":
        # 수정본 안 provenance 주석은 본문이 아니다 — 매칭 전에 제거
        revised = re.sub(r"<!--[\s\S]*?-->", "", revised)
        rev_norm = normalize(revised)
        # 파일 상단 러너 주석(원문 인용 가능)도 rest에서 제외
        rest_norm = normalize(re.sub(r"<!--[\s\S]*?-->", "", rest_raw))
        # 1) planted — 수정본에서 사라졌으면 '적용', 남았지만 기록에 올렸으면 '보류'(둘 다 잡은 것)
        if planted:
            caught, missed = [], []
            for p in planted:
                m = normalize(p["match"])
                if m not in rev_norm:
                    caught.append((p, "적용"))
                elif m in rest_norm:
                    caught.append((p, "보류/제안"))
                else:
                    missed.append(p)
            recall = len(caught) / len(planted)
            thr = thresholds.get("recall_min")
            ok = thr is None or recall >= thr
            napply = sum(1 for _, s in caught if s == "적용")
            print(f"[탐지] 잡음 {len(caught)}/{len(planted)} = {recall:.2f}"
                  f" (적용 {napply} · 보류 {len(caught) - napply})"
                  + (f" (기준 {thr}) {'PASS' if ok else 'FAIL'}" if thr is not None else ""))
            for p in missed:
                print(f"  - 놓침 {p['id']}: “{p['span']}” ({p['type']})")
            if not ok:
                failures.append("recall")
        # 2) trap — 수정본에 원문 그대로 남아 있어야 한다. 부재 = 즉시 FAIL
        for t in traps:
            if normalize(t["match"]) in rev_norm:
                print(f"[분별] trap 보존 {t['id']} — PASS")
            else:
                print(f"[분별] ✗ trap 훼손 {t['id']}: “{t['match']}” 이 수정본에 없다 — FAIL")
                print(f"        보존 이유: {t['reason']}")
                failures.append(f"trap:{t['id']}")
        for b in exp.get("known_borderline", []):
            status = "보존" if normalize(b["span"][:12]) in rev_norm else "수정/삭제(저자 판정 대상이었음 — 기록 확인)"
            print(f"[경계] {status}: “{b['span'][:30]}…”")
        # 3) 변경 기록표 + 적용 건수(클린 대조군 노이즈)
        log = extract_section(result_raw, "변경 기록") or result_raw
        rows = table_rows(log)
        applied = [r for r in rows if any("적용" in c and "보류" not in c for c in r)]
        held = [r for r in rows if any(c.strip().startswith("보류") for c in r)]
        original = re.sub(r"<!--[\s\S]*?-->", "", (case_dir / "input.md").read_text(encoding="utf-8"))
        empty_log_is_explicit_no_change = (
            not rows
            and normalize(original).strip() == rev_norm.strip()
            and re.search(r"(?m)^\|\s*유형\s*\|\s*before\s*\|\s*after\s*\|\s*이유\s*\|\s*상태\s*\|\s*$", log)
            and re.search(r"적용\s*0건", log)
            and re.search(r"보류(?:\s*제안)?\s*0건", log)
        )
        print(f"[형식] 변경 기록 {len(rows)}행 (적용 {len(applied)} · 보류 {len(held)})"
              + (" — 원문 동일·변경 없음 명시 PASS" if empty_log_is_explicit_no_change
                 else " — 기록표 없음(형식 위반?)" if not rows else ""))
        if not rows and not empty_log_is_explicit_no_change:
            failures.append("format")
        max_flags = thresholds.get("max_total_flags")
        if max_flags is not None and len(applied) > max_flags:
            print(f"[분별] 적용 {len(applied)}건 > 상한 {max_flags} — FAIL (사람이 다듬은 원고 과잉 수정)")
            failures.append("noise")
        # 4) 문체 — 수정본에서 존댓말 전환 탐지(인용 블록 '>' 줄 제외)
        if exp.get("tone") == "~한다":
            prose = [l for l in revised.splitlines() if not l.strip().startswith(">")]
            polite = polite_sentences(prose)
            if polite:
                print(f"[문체] 수정본에 존댓말 의심 {len(polite)}건(사람 확인 필요):")
                for s in polite[:5]:
                    print(f"  - {s[:60]}")
                failures.append("tone-review")
            else:
                print("[문체] 존댓말 전환 없음 — PASS")
    else:
        result = normalize(result_raw)
        # 1) planted 회수율(검토표에 등장)
        if planted:
            found = [p for p in planted if normalize(p["match"]) in result]
            recall = len(found) / len(planted)
            thr = thresholds.get("recall_min")
            ok = thr is None or recall >= thr
            print(f"[탐지] recall {len(found)}/{len(planted)} = {recall:.2f}"
                  + (f" (기준 {thr}) {'PASS' if ok else 'FAIL'}" if thr is not None else ""))
            for p in planted:
                if p not in found:
                    print(f"  - 놓침 {p['id']}: “{p['span']}” ({p['type']})")
            if not ok:
                failures.append("recall")
        # 2) trap 잠재 오탐 — 등장 = 사람 확인 대상(이유란 '보존' 언급일 수 있음)
        for t in traps:
            if normalize(t["match"]) in result:
                print(f"[분별] ⚠ trap 등장(사람 확인 필요) {t['id']}: “{t['match']}”")
                print(f"        보존 이유: {t['reason']}")
                failures.append(f"trap-review:{t['id']}")
            else:
                print(f"[분별] trap 미등장 {t['id']} — PASS")
        for b in exp.get("known_borderline", []):
            status = "지적함(저자 판정 대기)" if normalize(b["span"][:12]) in result else "안 잡음(정답)"
            print(f"[경계] {status}: “{b['span'][:30]}…”")
        # 3) 형식 — 검토표 존재 + 총 지적 건수
        rows = table_rows(result_raw)
        print(f"[형식] 검토표 행 {len(rows)}건" + (" — 표 없음(형식 위반?)" if not rows else ""))
        max_flags = thresholds.get("max_total_flags")
        if max_flags is not None and len(rows) > max_flags:
            print(f"[분별] 총 지적 {len(rows)}건 > 노이즈 상한 {max_flags} — FAIL")
            failures.append("noise")
        # 4) after 문체
        if exp.get("tone") == "~한다":
            polite = polite_sentences(after_column(result_raw))
            if polite:
                print(f"[문체] after에 존댓말 의심 {len(polite)}건(사람 확인 필요):")
                for s in polite[:5]:
                    print(f"  - {s[:60]}")
                failures.append("tone-review")
            else:
                print("[문체] after 존댓말 전환 없음 — PASS")

    for j in exp.get("judge_items", []):
        print(f"[판정 필요] {j}")

    print("결과:", "요확인/실패 → " + ", ".join(failures) if failures else "프로그램 채점 전부 PASS")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
