# 세 스킬을 만드는 방법

`my-writing-skill`은 표현 점검·핵심 다듬기·독자 리뷰 스킬을 만드는 크리에이터입니다. 처음에는 기본 방식으로 시작할 수 있어요. 직접 준 점수와 이유가 쌓이면 각 스킬에 필요한 설정만 따로 남깁니다.

## 폴더 만들고 세 스킬 생성하기

```bash
python3 scripts/suite.py init local/my-writing --name my-writing
python3 scripts/suite.py build local/my-writing
python3 local/my-writing/skills/install.py codex
```

Claude Code는 마지막의 `codex`를 `claude`로 바꿔주세요. 생성된 스킬은 각각 독립적으로 설치해도 됩니다. 기본 설정으로 만든 것과 사용자에게 확인받은 지침은 각 폴더의 `build.json`에 구분해 남깁니다. 데이터셋을 내려받거나 모델을 실행하는 명령은 아닙니다.

## 1. 표현 점검 설정하기

`local/my-writing/expressions/examples.json`에서 예문 하나를 읽고 0·1·2점과 이유를 받습니다. 0은 어색해서 다시 볼 표현, 1은 보류, 2는 이 문맥에서 괜찮은 표현이에요. 예문의 점수이지 AI 작성 확률이 아닙니다. 단어만 평가하기보다 문장을 보여주세요.

예문을 `candidate.md`로 저장하고 실제 답을 받은 뒤 기록합니다.

```bash
python3 scripts/expression_preferences.py rate local/my-writing/expressions \
  --candidate local/my-writing/expressions/candidate.md --term '여정' \
  --score 0 --reason '내가 직접 말한 이유' --evidence '예문에 실제로 있는 여정이 포함된 구절' \
  --scope '이 예문이 쓰일 글'
```

위 값은 형식 예시입니다. 실제 예문과 답으로 바꿔주세요. 0점 표현은 `watch`, 2점 표현은 `preserve`의 문맥 참고어로 반영합니다. 1점은 보류합니다. 기본 키워드는 처음 읽어볼 위치일 뿐 저자가 싫어한다고 확정한 말이 아니에요. 같은 단어가 두 목록에 있어도 예문과 범위를 보고 판단합니다. 단어 전체를 점검하지 않기로 했다면 `base-checks.json`과 `checks.json`을 그 요청에 맞춰 바꿀 수 있습니다.

## 2. 핵심 문단과 이유 남기기

`local/my-writing/core/brief.md`에 이번 글에서 하고 싶은 말을 적습니다. 초안 한 문단을 같이 고치며 실제 점수와 이유를 받으세요. 0은 뜻이 안 보임, 1은 아직 부족함, 2는 잘 보임입니다. 점수를 대신 주거나 근사 점수를 정수로 바꾸지 않습니다.

기존 [점수와 지침 기록 방법](feedback-loop.md)의 `local/my-voice` 경로 대신 `local/my-writing/core`를 사용하면 됩니다. `record_rating.py`로 답을 남기고 `workspace.py propose`와 `confirm`으로 사용자에게 확인받은 지침만 남깁니다. `--rating 1`은 1점이 아니라 첫 번째 기록이에요. 새 문단에도 통하는지 따로 확인합니다.

## 3. 독자 고르고 워크숍 준비하기

`HF_HOME`을 기존 캐시 위치로 둔 상태에서 먼저 확인합니다.

```bash
python3 scripts/personas.py status
```

캐시가 없다면 경로와 용량을 안내하고 사용자의 확인을 받으세요. 확인 후 `prepare --download`를 실행합니다. 캐시가 있으면 새로 내려받지 않습니다. 라이브러리가 필요하면 아래 명령을 쓸 수 있어요.

```bash
uv run --with datasets --with pandas python scripts/personas.py candidates \
  --query '개발' --limit 10 --output local/my-writing/readers/candidates.json
python3 scripts/personas.py select --input local/my-writing/readers/candidates.json \
  --ids 실제_uuid_1 실제_uuid_2 --output local/my-writing/readers/selected.json
```

`실제_uuid`는 후보 목록에서 골라 바꿉니다. 골랐다면 `selected.json`을 같은 폴더의 `profiles.json`으로 복사하고 `reading-purpose.md`에 이번 글을 읽는 목적을 적어주세요. 개인 인물 설정은 공개 Git에 올리지 않습니다.

선택한 독자와 원고로 질문지를 만들 수 있어요.

```bash
python3 scripts/personas.py prompt --profiles local/my-writing/readers/profiles.json \
  --reader 실제_uuid_1 --passage local/draft.md --output local/my-writing/readers/first-review.md
```

질문지를 만든 것과 실제 응답을 받은 것은 다릅니다. [페르소나 응답 지침](persona-respondent.md)을 읽힌 별도 역할 대화로 응답을 받고 [워크숍 순서](reader-workshop.md)를 진행하세요. 해당 환경에 네모트론 persona-respondent 도구가 있다면 우선 사용합니다. 없다면 이 패키지의 지침을 적용한 독립 역할 응답으로 진행하고 실행 방식을 남깁니다.

## 바꾼 설정으로 다시 만들기

```bash
python3 scripts/suite.py build local/my-writing --output local/my-writing/skills-v2
```

기존 출력은 덮어쓰지 않습니다. 기존 스킬 링크를 해제하고 새 경로에서 설치할 수 있어요. 원고와 실제 평가는 유지합니다. 예전 버전의 통합 스킬을 계속 만들고 싶다면 `workspace.py build`도 그대로 쓸 수 있습니다.
