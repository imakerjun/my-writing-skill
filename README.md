# My Writing Skill

AI가 고쳐준 글인데, 막상 읽어보면 내가 쓰는 말과는 다를 때가 있어요. 매끄럽긴 한데 하고 싶었던 말이 빠지기도 하고요.

이 스킬과는 그 글을 놓고 이야기해볼 수 있습니다. 고치고 싶은 문단을 주면 AI가 한 번 고쳐 보여줘요. 읽어보고 어떤 말이 좋았는지, 어디가 어색했는지 알려주세요. 그 이유를 다음 글에도 참고할 수 있게 남깁니다.

## 한 문단만 가져와주세요

아직 초안이 없어도 괜찮아요. 누군가에게 설명하듯 말한 메모도 쓸 재료가 됩니다. 누구에게 무슨 말을 하고 싶은지 알려주면 그 이야기부터 시작해요.

나온 문단에는 이렇게 점수를 주세요.

- **0점 — 이건 아니다.** 어느 표현이 걸렸는지 말해주세요.
- **1점 — 애매하다.** 무엇이 달라지면 쓰고 싶을지 알려주세요.
- **2점 — 좋다.** 어떤 구절이 왜 마음에 들었는지 남겨주세요.

거창한 설명은 필요 없어요. “뜻은 맞는데 제가 동료한테 이렇게 말하진 않을 것 같아요”라고 해도 됩니다. 평소라면 어떻게 말할지 한마디 덧붙여주면 더 좋고요.

그 답을 듣고 AI가 다시 고칩니다. 다음 글에도 쓸 만한 기준이 나오면 지침으로 제안해요. 내 뜻과 맞는 것만 남기고, 다른 문단에도 써보세요. 어느 글에서는 좋았던 표현이 다른 글에서는 어색할 수도 있으니까요.

[실제로 나눠본 첫 대화](examples/first-conversation.md)도 볼 수 있어요.

## 설치하고 시작하기

Codex나 Claude Code, Python 3.10 이상이 필요해요. 따로 설치할 Python 패키지는 없습니다.

```bash
git clone https://github.com/imakerjun/my-writing-skill.git
cd my-writing-skill
python3 install.py codex
```

새 Codex 대화에서 아래처럼 시작해보세요.

```text
$my-writing-skill
이 문단을 내가 말하듯 고쳐보고 싶어.
후보 하나를 보여주면 내가 읽고 점수와 이유를 말할게.

[내 초안이나 말로 남긴 메모]
```

Claude Code를 쓴다면 마지막 명령을 `python3 install.py claude`로 바꾸고, `/my-writing-skill`로 시작하세요.

설치 후에도 이 저장소 폴더는 그대로 두세요. 스킬이 이 폴더를 찾아 읽습니다. 같은 이름의 다른 스킬을 덮어쓰지는 않아요. 설치를 해제하려면 `python3 install.py codex --uninstall`을 실행하면 됩니다.

어떤 글을 넣을지 막힌다면 [연습용 문단](examples/first-session.md)으로 먼저 해보세요.

## 익숙해지면 내 스킬로 남겨보세요

몇 번 같이 써보면 자주 고치는 표현이나 계속 살리고 싶은 문장이 생길 거예요. 내가 확인한 지침을 모아 `my-voice`처럼 내 이름의 스킬로 만들 수 있습니다. 만드는 명령은 [내 스킬로 남기는 방법](references/feedback-loop.md)에 있어요.

같은 표현을 자꾸 놓친다면 코드로 찾아볼 수도 있어요. 코드는 반복된 말과 위치를 찾고, AI는 앞뒤를 읽으며 어떻게 고칠지 살펴봅니다. 바뀐 글을 내 글에 쓸지는 직접 읽고 판단해주세요.

내가 전하려던 뜻이 독자에게도 보이는지 궁금할 때는 [독자 리뷰](references/reader-review.md)를 받아보세요. 실제 사람에게 부탁하거나, AI에게 독자 역할을 맡겨 미리 살펴볼 수 있어요. AI의 리뷰는 실제 독자의 답과 구분해 남깁니다.

<details>
<summary>도구와 기록을 더 살펴보고 싶다면</summary>

- [자주 살펴보는 표현](references/review-signals.md)과 [코드가 세는 범위](references/signals.md)
- [테스트를 만들고 확인하는 방법](eval/README.md)과 [현재 검사 기록](eval/status.json)
- [이 스킬이 만들어진 과정](references/origin.md)과 [참고한 공식 문서](references/sources.md)
- [글 샘플로 문체 스킬을 만드는 별도 도구](https://github.com/imakerjun/humanizer-skill-creator)

개인 글과 점수는 `local/`에 두며 Git에서 제외돼요. 만든 개인 스킬에도 내 글과 평가가 들어갈 수 있으니, 공유하기 전에는 내용을 확인해주세요. 여기서 바꾸는 것은 AI에게 줄 지침과 참고 내용입니다. 모델 자체를 다시 학습시키지는 않아요.

예전 `saramnaemsae-skill` 폴더를 쓰고 있다면 아래 명령으로 저장소 주소를 바꾼 뒤 업데이트할 수 있어요.

```bash
git remote set-url origin https://github.com/imakerjun/my-writing-skill.git
```

</details>

MIT 라이선스입니다. 본인 글에 맞게 고쳐서 써보세요.
