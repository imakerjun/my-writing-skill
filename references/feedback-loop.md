# 좋았던 이유를 내 스킬에 남겨보세요

대화에서 ‘이 문장이 좋다’고 했던 이유를 다음 글에서도 쓰고 싶을 때 따라 해보세요. 아래 명령은 기록을 저장하고 스킬 파일을 만듭니다. 모델을 직접 호출하지는 않아요. 명령은 이 저장소를 내려받은 폴더에서 실행해주세요. 개인 기록을 두는 `local/`은 Git에서 제외됩니다.

## 1. 기록할 폴더를 만듭니다

```bash
python3 scripts/workspace.py init local/my-voice --name my-voice
```

`brief.md`에 누구에게 무슨 말을 전할지 적어주세요. `checks.json`의 `watch`와 `preserve`는 빈 목록으로 시작해요. 내 글을 보면서 자꾸 고치는 표현이 생기면 그때 하나씩 넣으면 됩니다.

## 2. 내가 준 점수와 이유를 남깁니다

후보를 `local/my-voice/candidate-01.md`에 저장한 뒤, 실제로 준 점수와 이유를 적어주세요.

```bash
python3 scripts/record_rating.py local/my-voice/candidate-01.md \
  --score 1 --evidence '후보에 실제로 있는 구절' \
  --reason '내가 직접 말한 이유' --output local/my-voice/ratings.jsonl
```

위 구절과 이유는 명령 형식을 보여주는 예시예요. 내가 읽은 후보와 내 답으로 바꿔 넣어주세요. 후보에 없는 구절은 기록할 수 없습니다. ‘2점에 가까워요’처럼 답했다면 우선 대화 원문으로 남겨두세요. 이 명령은 정수 점수만 받습니다.

## 3. 다음에 어떻게 쓰면 좋을지 제안받습니다

AI에게 이유를 읽고 지침과 확인 질문을 제안해달라고 하세요. 어디에 쓸 지침인지, 예외는 무엇인지도 함께 남깁니다. 아래는 명령 형식 예시이니, 제안받은 내용으로 바꿔주세요.

```bash
python3 scripts/workspace.py propose local/my-voice --rating 1 \
  --instruction '다음 행동을 일반적인 당부 대신 실제로 할 일로 쓴다.' \
  --scope '동료에게 다음 작업을 안내하는 문단' \
  --exception '행동을 권하지 않는 기록이나 묘사' \
  --question '읽고 나서 실제로 무엇을 하면 되는지 문장 안에 보이는가?'
```

`--rating 1`은 점수 1점이 아니라 **`ratings.jsonl`의 첫 번째 기록**을 뜻해요. 그 기록의 이유와 근거 구절, 후보 해시를 함께 보관합니다. 아직 제안 상태인 `proposed`로 저장돼요.

지침을 읽어보고 내 뜻과 맞으면 확인해주세요. 대화에서 이미 반영해달라고 했다면 AI가 그 요청에 따라 확인할 수 있습니다.

```bash
python3 scripts/workspace.py confirm local/my-voice --rule r001
```

확인한 지침만 다음 단계에서 내보냅니다.

## 4. 내 스킬을 만들고 설치합니다

```bash
python3 scripts/workspace.py build local/my-voice
python3 local/my-voice/skill/my-voice/install.py codex
```

Claude Code에 설치하려면 마지막의 `codex`를 `claude`로 바꿔주세요. 새 대화에서 `$my-voice` 또는 `/my-voice`로 부르면 됩니다. 확인한 지침과 이유, 이번 글의 메모, 점검할 표현, 독자 리뷰 방법과 평가 질문이 들어 있어요. 원래 저장소 없이도 설치해서 쓸 수 있습니다.

다시 만들 때는 기존 출력 폴더를 덮어쓰지 않아요. 새 경로를 지정해주세요.

```bash
python3 scripts/workspace.py build local/my-voice --output local/my-voice/skill-v2/my-voice
```

기존 스킬 설치기의 `install.py codex --uninstall`로 링크를 해제한 뒤, 새로 만든 스킬의 설치기를 실행하세요. 원고와 평가 기록은 그대로 남습니다.

## 5. 다른 문단에 써봅니다

AI에게 확인한 지침과 `eval/criteria.json`을 읽히고, 아직 같이 고쳐보지 않은 문단에 적용해달라고 하세요. 나온 글을 읽고 다시 점수와 이유를 남깁니다.

앞에서는 괜찮았는데 이번에는 어색할 수 있어요. 그럴 때는 적용할 상황이나 예외를 바꿔보세요. 그 문단으로 지침을 고쳤다면, 다음 확인에는 또 다른 문단을 써봅니다.

이렇게 남긴 기록은 다음 글을 쓸 때 참고하는 지침이에요. 모델의 가중치를 학습시키는 과정은 아닙니다. 점수가 쌓였다는 사실만으로 글쓰기 실력이 늘었다고 결론 내리기도 어렵고요. 새 글에서도 내 의도가 잘 보이는지 계속 읽어봐주세요.
