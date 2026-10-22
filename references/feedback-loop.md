# 점수와 이유를 설치 가능한 내 스킬로

이 명령은 모델을 호출하지 않는다. 대화에서 받은 평가를 기록하고 확인한 지침을 모아 스킬 파일을 만든다. 명령은 저장소를 clone한 폴더에서 실행한다. `local/`은 git에서 제외된다.

## 1. 내 작업 폴더

```bash
python3 scripts/workspace.py init local/my-voice --name my-voice
```

`brief.md`에 이번 글의 독자·전할 뜻·기대하는 행동·살릴 재료를 적는다. `checks.json`은 빈 `watch`·`preserve` 목록으로 시작한다. 남의 금지어 목록을 내 취향으로 복제하지 않는다.

## 2. 실제 점수와 이유

후보를 `local/my-voice/candidate-01.md`에 저장하고 저자의 실제 답을 받은 뒤 기록한다.

```bash
python3 scripts/record_rating.py local/my-voice/candidate-01.md \
  --score 1 --evidence '후보에 실제로 있는 구절' \
  --reason '내가 직접 말한 이유' --output local/my-voice/ratings.jsonl
```

위 값은 명령 형식 예시다. 점수·구절·이유를 실제 답으로 바꾼다. 근거 구절이 후보에 없으면 기록기가 거절한다. 2점에 가까움 같은 답은 대화 원문으로 남기고 정수 기록기에 넣지 않는다.

## 3. 이유를 지침과 질문으로

LLM이 이유를 읽고 지침·적용 범위·예외·eval 질문을 제안한다. 다음은 형식 예시이며 확정된 사용자 기준이 아니다.

```bash
python3 scripts/workspace.py propose local/my-voice --rating 1 \
  --instruction '다음 행동을 일반적인 당부 대신 실제로 할 일로 쓴다.' \
  --scope '동료에게 다음 작업을 안내하는 문단' \
  --exception '행동을 권하지 않는 기록이나 묘사' \
  --question '읽고 나서 실제로 무엇을 하면 되는지 문장 안에 보이는가?'
```

`--rating 1`은 `ratings.jsonl`의 첫 줄이다. 이유 원문·근거 구절·후보 해시를 지침과 함께 보존한다. 상태는 `proposed`다. 저자가 이 지침을 쓰겠다고 확인한 다음에만 실행한다.

```bash
python3 scripts/workspace.py confirm local/my-voice --rule r001
```

확인하지 않은 지침은 내보내지 않는다. 같은 이유가 다른 장에서도 통하는지는 새 문단에서 확인한다. 점수를 저장하는 것과 다음 작업에 그 기준을 다시 읽히는 것은 별개다.

## 4. 내 스킬 만들기와 설치

```bash
python3 scripts/workspace.py build local/my-voice
python3 local/my-voice/skill/my-voice/install.py codex
```

Claude Code는 마지막의 `codex`를 `claude`로 바꾼다. 새 대화에서 `$my-voice` 또는 `/my-voice`를 사용한다. 확인한 기준과 이유, 이번 장의 브리프, 개인 점검어, 독자 리뷰 지침, 평가 질문이 들어 있다. 원래 저장소 없이 설치할 수 있다.

기존 스킬은 덮어쓰지 않는다. 다시 만들 때는 `build ... --output local/my-voice/skill-v2/my-voice`처럼 새 경로를 지정한다. 기존 설치기의 `install.py codex --uninstall`로 링크를 해제한 뒤 새 스킬 설치기를 실행한다. 원고·평가는 지우지 않는다.

## 5. 다른 문단으로 확인

확인된 지침과 `eval/criteria.json`을 읽고 개발에 쓰지 않은 문단에 적용한다. 저자가 다시 점수와 이유를 남긴다. 1점이었다면 무엇이 더 드러나야 2점인지 살핀다. 지침이 과하면 적용 범위나 예외를 바꾸고 또 다른 문단으로 확인한다.

이미 본 문단을 다시 고쳐 통과한 것과 다른 문단에도 통하는 것은 다르다. 점수의 누적을 모델 가중치 학습이나 미감 향상의 실증 결과로 부르지 않는다.
