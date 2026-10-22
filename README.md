# My Writing Skill

**한 문단을 같이 고치며, 내 판단이 들어간 글쓰기 스킬을 만듭니다.**

AI에게 초안을 받고 0·1·2점과 이유를 남깁니다. 그 이유에서 지침과 확인 질문을 만들고, 다른 문단에서 다시 써봅니다. 확인한 기준은 **내 이름의 스킬 폴더**로 만들어 Codex나 Claude Code에 설치할 수 있습니다.

임동준의 우아콘 발표 「AI에게 미감을 가르칠 수 있을까?」에서 소개한 사람냄새 스킬에서 출발했습니다. 발표자의 금지어와 말투를 복제하기보다 **내가 무엇을 전하고 싶은지, 어떤 문장을 왜 좋다고 느끼는지**를 구체화합니다.

## 지금 시작하기

준비물은 **초안 한 문단**입니다. 글로 정리가 안 됐다면 음성으로 말한 메모도 됩니다. 전할 뜻이 아직 모호해도 대화에서 같이 좁혀갑니다. 코드 도구는 Python 3.10 이상, 추가 패키지 없이 실행됩니다.

```bash
git clone https://github.com/imakerjun/my-writing-skill.git
cd my-writing-skill
python3 install.py codex
```

새 Codex 대화에서 아래처럼 시작하세요.

```text
$my-writing-skill
내 글쓰기 스킬을 만들고 싶어. 이 메모부터 한 문단으로 같이 다듬자.
전할 뜻이 모호하면 질문 하나씩 해줘.
후보 하나를 보여주면 내가 0·1·2점과 이유를 말할게.
그 이유를 다음 지침과 eval 질문으로 남기고, 다른 문단에도 써보자.

[내 초안 또는 말로 풀어 쓴 메모]
```

Claude Code는 `python3 install.py claude` 후 `/my-writing-skill`로 시작합니다. 설치기는 링크만 만들며 같은 이름의 다른 스킬을 덮어쓰지 않습니다. 해제는 `python3 install.py codex --uninstall`입니다.

## 발표에서 보여준 세 가지 협업

| 협업 | 하는 일 | 이 저장소에서 쓰는 것 |
|---|---|---|
| **코드 × LLM** | 자꾸 고치는 표현과 반복 위치를 찾고, 문맥을 보고 수정·보존·보류 | [분석기](scripts/analyze.py), 개인 `checks.json`, [표현 점검 후보](references/review-signals.md) |
| **나 × LLM** | 전할 뜻과 표현 방향을 같이 다듬고, 후보 하나에 점수와 이유 남기기 | [장별 브리프](templates/brief.md), [평가 기록기](scripts/record_rating.py), [개인 스킬 생성기](scripts/workspace.py) |
| **독자 역할 × 편집 역할** | 독자가 이해한 뜻과 걸린 문장을 받고, 반영할 리뷰를 선택해 수정·재리뷰 | [독자 리뷰 절차](references/reader-review.md), [프로필 틀](templates/reader-profile.json) |

**내 점수와 이유 → 스킬 지침·eval 질문 → 다른 문단에서 다시 확인.** 설치만으로 이 전체 과정이 자동 실행되지는 않습니다. LLM의 후보와 내가 하는 판단을 대화로 잇습니다.

## 내 기준과 이번 장의 의도를 나눕니다

‘사실과 화자를 유지한다’, ‘내가 좋다고 느낀 표현을 남긴다’는 공통 기준입니다. 반면 **이번 글에서 무엇을 전할지, 독자가 무엇을 해보길 바라는지, 어떤 경험을 살릴지**는 글·장마다 달라집니다. 그때마다 브리프를 바꿉니다.

정리된 생각이 없다면 LLM과 서로 다른 전개를 비교해보세요. 실제 장면으로 시작할지, 질문으로 시작할지, 말의 뜻을 풀어볼지 선택할 수 있습니다. 핵심 문단부터 만들고 길게 확장합니다. 표현을 다듬는 동안 생각도 더 분명해질 수 있지만, 이를 측정된 사고력 향상으로 주장하지는 않습니다.

## 0·1·2점이 내 스킬이 되는 과정

| 점수 | 내 반응 | 다음에 할 일 |
|---|---|---|
| **0** | 이건 아니다 | 어느 구절이 내 뜻과 다른지, 내가 말로 설명하면 어떻게 말할지 알려주기 |
| **1** | 애매함 | 무엇이 빠졌고 어떻게 달라지면 좋을지 한 가지 짚기 |
| **2** | 좋다 | 어떤 구절에서 무엇이 드러나 좋았는지 남기기 |

점수만 높이는 것이 목표는 아닙니다. 이유 원문과 적용할 맥락을 남기고, 다음 문단에서도 통하는지 확인합니다. AI가 저자 대신 점수나 채택을 정하지 않습니다. ‘2점에 가까움’은 확정 2점으로 바꾸지 않습니다.

파일로 남기려면 개인 작업 폴더를 만듭니다.

```bash
python3 scripts/workspace.py init local/my-voice --name my-voice
```

스킬에게 이 폴더를 알려주고 초안·점수·이유를 남기세요. 확인한 지침이 생겼다면 다음 명령으로 내 스킬을 만듭니다.

```bash
python3 scripts/workspace.py build local/my-voice
python3 local/my-voice/skill/my-voice/install.py codex
```

새 대화에서 `$my-voice`로 사용합니다. 생성 폴더에는 확인한 지침과 이유, 장별 브리프, 코드 분석기, 독자 리뷰 절차, eval 질문이 함께 들어 있습니다. 원래 저장소 없이 독립적으로 설치할 수 있습니다.

**미확인 지침은 내보내지 않고, 기존 출력 폴더는 덮어쓰지 않습니다.** 평가 기록→지침 제안→확인→내보내기의 실제 명령은 [단계별 사용법](references/feedback-loop.md)에 있습니다. 개인 파일은 `local/`에 두며 공개 저장소에 자동으로 올리지 않습니다.

## 자꾸 고치는 표현은 코드가 찾게 합니다

개인 `checks.json`에서 점검할 표현을 바꿉니다. 다음 목록은 설정 형식 예시입니다.

```json
{
  "watch": ["결국", "매우"],
  "preserve": ["우리 팀", "그래서"]
}
```

```bash
python3 scripts/analyze.py local/my-voice/draft.md \
  --config local/my-voice/checks.json --output local/my-voice/before.json
```

`watch`는 삭제 지시가 아니라 문맥을 다시 볼 위치입니다. `preserve`도 모든 문맥의 자동 보존 판정이 아닙니다. 코드로 찾고 LLM과 문맥을 살핀 뒤, 같은 설정으로 재검사합니다. 접속사·부사·글자 수를 줄였다고 더 좋은 글이라고 판정하지 않습니다. [코드가 실제로 세는 범위](references/signals.md)를 확인하세요.

## 원하는 독자를 고릅니다

장마다 예상 독자는 달라질 수 있습니다. 그 독자가 이미 아는 것과 읽는 목적을 정하고, “어떤 뜻으로 읽었는지, 어느 구절에서 멈췄는지”를 묻습니다. 모든 리뷰를 반영하면 글의 방향이 흐려질 수 있으니 내 의도에 맞는 중요한 리뷰 하나부터 반영하고 다시 읽힙니다.

실제 독자에게 물을 수도 있고 LLM에 독자 역할을 맡길 수도 있습니다. Nemotron Personas Korea를 사용하려면 별도의 실제 데이터 행·출처가 필요합니다. 임의 설정을 Nemotron 표본으로 부르지 않습니다. 합성 리뷰는 예상 질문을 찾는 자료이며 실제 사람의 반응이나 선호율이 아닙니다. [독자 선정과 재리뷰 방법](references/reader-review.md)을 참고하세요.

## expected.json, planted, traps는 무엇인가요?

**`expected.json`은 이 테스트에서 기대하는 결과를 적은 파일입니다.** 그 안의 필드 이름은 이 저장소의 채점기가 정한 형식입니다. 앤트로픽 표준 스키마가 아니며 `expected`라는 키가 필수인 것도 아닙니다.

| 필드 | 뜻 | 확인하는 것 |
|---|---|---|
| `planted` | **고칠 표현** | 의도적으로 넣은 문제 표현을 수정하거나 보류 기록했는가 |
| `traps` | **남길 표현** | 실수로 고치기 쉬운 정상 표현을 수정본 본문에 보존했는가 |
| `judge_items` | **문맥에서 볼 질문** | 뜻·자연스러움·저자 의도는 코드 외의 판단으로 확인 |

모델에는 입력·저자 맥락만 주고 기대 결과는 숨깁니다. 실제 응답을 받은 뒤 `scripts/grade.py`로 채점합니다. 공개용 가상 사례 3개가 있고, `workspace.py eval-case`로 자기 사례도 만들 수 있습니다. [직접 만드는 방법](eval/README.md)을 보세요.

```bash
python3 scripts/grade.py eval/cases/01-repetition local/eval-run/01.md
python3 -m unittest discover -s tests -v
```

코드 PASS는 의미·자연스러움·저자 만족을 모두 검증했다는 뜻이 아닙니다. 모델 실행과 프로그램 테스트, 저자 평가를 구분한 현재 상태는 [eval/status.json](eval/status.json)에 남깁니다. 이전 v0.1.0 실행 기록은 당시 버전·해시를 보존하며 새 버전의 효과로 옮기지 않습니다.

## 내 파일과 공개 자료

- `SKILL.md`: 공통 진행 방식. 본인의 취향을 모든 사용자에게 적용하는 파일로 직접 바꿀 필요는 없습니다.
- `local/my-voice/brief.md`: 이번 글·장의 독자와 뜻.
- `local/my-voice/profile.json`, `ratings.jsonl`: 내 확인 상태·점수·이유.
- `local/my-voice/checks.json`: 내 코드 점검어.
- `local/my-voice/skill/my-voice/`: 생성한 개인 스킬. 개인 글·평가가 들어 있으므로 공유 여부는 직접 결정합니다.

미공개 책 원고·실제 저자 평가·페르소나 데이터·인터뷰 원답은 공개 패키지에 넣지 않습니다. 이 과정은 프롬프트·맥락을 갱신하는 방법이며 모델 파인튜닝이 아닙니다.

기존 `saramnaemsae-skill` clone은 `git remote set-url origin https://github.com/imakerjun/my-writing-skill.git` 후 업데이트할 수 있습니다. 기존 개인 파일은 유지됩니다. 설치기는 이 저장소의 예전 링크만 옮기고 다른 스킬은 덮어쓰지 않습니다.

[첫 대화 가이드](references/first-session.md) · [실행해볼 예시](examples/first-session.md) · [원본과 공개판](references/origin.md) · [공식 근거](references/sources.md) · [샘플로 문체 스킬을 만드는 별도 도구](https://github.com/imakerjun/humanizer-skill-creator)

MIT 라이선스. 본인의 글과 기준에 맞게 수정해 사용할 수 있습니다.
