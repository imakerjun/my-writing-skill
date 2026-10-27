---
name: {{name}}
description: Nemotron Personas Korea의 실제 행에서 독자를 고르고 원고 리뷰와 질문을 진행한다. 저자 워크숍 순서로 이해한 뜻·좋았던 구절·개선 제안을 받고 저자가 고른 피드백으로 다시 읽힌다.
metadata:
  version: "1"
---

# 독자 리뷰

[독자 선정과 워크숍](references/reader-workshop.md)을 읽는다. 합성 페르소나의 응답은 LLM의 역할 응답이며 실제 사람의 반응이나 선호율로 소개하지 않는다. [대화 말투](references/first-session.md)를 따르고 원고와 읽을 사람의 목적부터 확인한다.

## 데이터 준비와 독자 선정

`references/selected-readers.json`에 이미 선택한 행이 있고 이번 요청에 맞는 독자라면 그 자료로 바로 읽힌다. 선택된 행으로 대화할 때는 전체 데이터셋이나 캐시를 다시 요구하지 않는다. 새 독자를 찾거나 데이터 원본을 확인할 때 아래 준비 절차를 진행한다.

먼저 `python3 scripts/personas.py status`로 `HF_HOME`과 캐시의 전체 shard를 확인한다. 환경 변수가 없으면 기존 Hugging Face 캐시 위치를 찾아 사용자에게 확인하거나 `--cache-dir`로 명시한다. 새 위치에 조용히 중복 다운로드하지 않는다.

캐시가 없거나 불완전하면 위치·용량(압축 약 1.85GB, 추가 변환 캐시를 포함하면 약 5.76GB)을 알려주고 확인을 받는다. 승인받은 뒤에만 `prepare --download`를 실행한다. 필요한 라이브러리가 없으면 `uv run --with datasets --with pandas python scripts/personas.py ...`를 쓸 수 있다. 기존 `HF_HOME`을 유지한다.

`candidates --query 검색어 --limit 10 --output 후보.json`으로 실제 행을 찾고, 읽는 목적·이미 아는 것·관련 경험을 보고 필요한 수의 독자를 고른다. 검색은 단어 일치이며 모집단을 대표하는 표본이 아니다. `select --input 후보.json --ids uuid1 uuid2 --output 독자.json`으로 선택을 남긴다. 데이터셋 uuid·revision·사용 필드를 보존한다. 실제 행을 못 찾았으면 임의의 일반 인물을 Nemotron 표본으로 대신하지 않는다.

## 함께 읽고 질문하기

`prompt --profiles 독자.json --reader uuid --passage 원고.md --output 질문.md`로 읽을 자료를 준비한다. 역할 응답에는 [페르소나 응답 지침](references/persona-respondent.md)을 적용한다. 독자가 여러 명이면 첫 반응은 서로의 답을 보지 않고 작성하게 한다.

처음에는 저자의 기대 답을 주지 않고, 이해한 뜻을 요약하게 한다. 이어서 좋았던 구절과 이유, 고치면 좋을 구절과 제안을 받는다. 저자는 먼저 듣고 메모한 뒤 궁금한 점을 질문한다. 사용자가 원하면 독자와 한 질문씩 대화를 이어간다. 실제 기록에 없는 독자의 발언을 이미 받은 리뷰처럼 만들지 않는다.

저자는 ‘이 리뷰를 반영할 만한가’를 0=반영하지 않음, 1=보류, 2=반영할 만함으로 평가한다. 원고 점수와 구분해 `scripts/record_rating.py`로 리뷰 원문·근거 구절·이유를 남길 수 있다. AI가 저자 점수나 승인을 대신 정하지 않는다. 중요한 리뷰 하나부터 반영한 후보를 만들고, 같은 독자에게 다시 읽혀 처음과 달라진 점을 확인한다. 원하지 않는 자동 반복을 계속하지 않는다.

{{personal_notes}}
