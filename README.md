# My Writing Skill

발표에서 본 세 가지 협업을 내 글에도 써보고 싶다면, 이 스킬과 함께 만들어보세요. **자꾸 고치는 표현을 찾는 스킬, 전하고 싶은 말을 찾는 스킬, 독자에게 읽혀보는 스킬**을 각각 만들 수 있어요.

처음부터 나만의 글쓰기 원칙을 정리할 필요는 없습니다. 예문이나 내 초안을 읽고 “이건 어색해요”, “이 문장은 쓰고 싶어요”라고 말해보세요. 어떤 구절 때문에 그렇게 느꼈는지 함께 남기면, 다음 글에서도 참고할 설정과 지침이 됩니다.

## 어떤 스킬을 만들 수 있나요?

### 1. AI 냄새 표현 점검

내가 자꾸 고치는 말을 코드가 찾게 합니다. 기본 키워드와 예문이 준비돼 있어요. 하나씩 읽고 **0점은 어색해요, 1점은 애매해요, 2점은 괜찮아요**로 답해보세요.

점수와 이유는 단어뿐 아니라 예문과 함께 남깁니다. “성장을 확인하는 자리”는 어색해도 “의자를 제자리에”는 필요할 수 있으니까요. 코드는 그 말이 나온 위치와 횟수를 찾고, LLM은 앞뒤를 읽으며 고칠지 살릴지 살펴봅니다.

### 2. 핵심 다듬기

하고 싶은 말이 있는데 글로 쓰면 흐려질 때 같이 써보세요. 누구에게 무슨 말을 전할지, 그 말을 보여줄 경험과 근거는 무엇인지 이야기합니다. 질문으로 시작할지, 실제 장면을 보여줄지처럼 풀어가는 방법도 비교할 수 있어요.

한 문단부터 써보고 **0점은 뜻이 안 보여요, 1점은 아직 부족해요, 2점은 잘 보여요**로 답합니다. 좋거나 걸린 이유로 다음 지침을 만들고, 다른 문단에서도 통하는지 확인해요.

### 3. 독자 리뷰

[NVIDIA Nemotron Personas Korea](https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea)의 실제 행에서 이번 글을 읽을 독자를 고릅니다. 데이터가 이미 있으면 그 캐시를 쓰고, 없다면 저장 위치와 용량부터 확인해요.

독자가 이해한 뜻, 좋았던 구절, 막힌 곳을 듣고 궁금한 점을 물어봅니다. 저자 워크숍처럼 먼저 듣고 나서 질문해보는 방식이에요. 리뷰에는 **0점은 반영하지 않을래요, 1점은 보류할래요, 2점은 반영할 만해요**로 답하고, 중요한 것부터 고쳐 다시 보여줍니다. 독자는 실제 사람이 아닌 합성 인물이며, 응답은 LLM이 그 역할로 작성해요.

## 설치하고 말 걸어보세요

Codex나 Claude Code, Python 3.10 이상이 필요합니다. 스킬 생성과 표현 점검에는 따로 설치할 Python 패키지가 없어요.

```bash
git clone https://github.com/imakerjun/my-writing-skill.git
cd my-writing-skill
python3 install.py codex
```

새 Codex 대화에서 이렇게 시작해보세요.

```text
$my-writing-skill
내 글에 맞는 표현 점검, 핵심 다듬기, 독자 리뷰 스킬을 만들고 싶어.
먼저 예문 하나를 보여줘. 내가 점수와 이유를 말할게.
```

Claude Code는 마지막 명령을 `python3 install.py claude`로 바꾸고 `/my-writing-skill`로 시작하면 됩니다. 설치 후에도 이 폴더는 그대로 두세요. 스킬이 여기 있는 안내와 도구를 읽습니다.

급하다면 기본 설정으로 먼저 세 스킬을 만들 수도 있어요. 내가 확인한 취향과 기본 설정은 구분해 남깁니다. 세 개를 모두 만들거나 쓰지 않아도 됩니다.

## 만든 뒤에는 이렇게 불러요

기본 이름으로 만들었다면 각각 이렇게 쓸 수 있어요.

```text
$my-writing-expressions 이 문단에서 자꾸 고치는 표현을 찾아줘.
$my-writing-core 이 글에서 꼭 전할 말을 같이 찾아보자.
$my-writing-readers 이 글을 읽을 독자를 고르고 리뷰를 받아보자.
```

후보를 읽고 점수와 이유를 말해주세요. 그 이유를 남기고 다시 써보는 과정을 반복합니다. 내 뜻에 맞는 지침만 확인하고, 다른 글에서 어색하면 고쳐도 돼요.

[예문으로 세 스킬 만들어보기](examples/three-skills.md) · [명령과 파일을 자세히 보기](references/creator.md)

<details>
<summary>직접 명령을 실행하거나 기록을 살펴보고 싶다면</summary>

```bash
python3 scripts/suite.py init local/my-writing --name my-writing
python3 scripts/suite.py build local/my-writing
python3 local/my-writing/skills/install.py codex
```

각 스킬은 독립적으로 설치할 수 있어요. 바뀐 설정으로 다시 만들 때는 `build ... --output 새경로`를 사용합니다. 기존 출력은 덮어쓰지 않습니다. 각 설치기의 `--uninstall`로 링크를 해제할 수 있어요.

독자 데이터를 읽는 도구에는 추가 라이브러리가 필요할 수 있습니다. `uv run --with datasets --with pandas python scripts/personas.py ...`로 실행할 수 있어요. 기존 `HF_HOME`을 유지합니다. 데이터가 없으면 압축 약 1.85GB, 변환 캐시까지 쓰는 방식은 약 5.76GB의 공간이 필요할 수 있으니 위치를 확인한 뒤 내려받으세요. 데이터셋 자체는 이 저장소에 포함하지 않습니다.

- [표현 예시](references/review-signals.md)와 [코드가 세는 범위](references/signals.md)
- [독자 워크숍 진행](references/reader-workshop.md)
- [테스트 방법](eval/README.md)과 [현재 검사 기록](eval/status.json)
- [만들어진 과정](references/origin.md)과 [참고한 자료](references/sources.md)

개인 원고와 실제 점수, 선택한 인물 설정은 `local/`에 두며 Git에서 제외돼요. 생성한 스킬에도 이 내용이 들어갈 수 있으니 공유하기 전에는 확인해주세요. AI가 대신 준 점수나 모의 평가를 실제 저자의 평가로 저장하지 않습니다.

예전 통합 스킬을 만들던 `workspace.py`도 계속 쓸 수 있어요. 예전 저장소 이름을 쓰고 있다면 `git remote set-url origin https://github.com/imakerjun/my-writing-skill.git`로 주소를 바꿀 수 있습니다.

</details>

MIT 라이선스입니다. 본인 글에 맞게 고쳐서 써보세요.
