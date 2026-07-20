---
name: setup-gemini-delegate
description: >-
  gemini-delegate 설치를 마무리하는 일회성 스킬. 자동 트리거("대량 작업 전 위임을
  먼저 검토하라")를 호스트 메모리 파일(Claude Code→CLAUDE.md, Codex→AGENTS.md)에
  마커 블록으로 넣고, Claude Code라면 탐색 위임 래퍼(Explore 서브에이전트)도 함께
  놓거나 뺀다. 사용자가 "/setup-gemini-delegate", "위임 자동 트리거 설치",
  "gemini-delegate 설치 마무리", "gemini-delegate 제거/삭제"라고 할 때 발동한다.
  gemini-delegate 스킬을 새로 설치한 직후에도 실행한다.
---

# gemini-delegate 설치 마무리 (setup-gemini-delegate)

이 스킬은 **위임 하네스가 아니다.** gemini-delegate 스킬 파일을 복사하는 것
(`npx skills add`)은 파일만 놓을 뿐, 스킬 배포 채널이 원칙적으로 건드리지 않는 두 자리를
비워 둔다 — 호스트 메모리 파일과 서브에이전트 디렉터리. 이 스킬이 그 둘을 넣고/뺀다.

1. **자동 트리거** — 오케스트레이터가 대량 작업 전 **스스로** 위임을 검토하게 만드는(능동 발동)
   한 줄. 호스트 메모리 파일에 마커 블록으로 들어간다. 배경 `docs/adr/0004`.
2. **탐색 위임 래퍼** — 탐색을 직접 하지 못하게 강제하는 `Explore` 서브에이전트.
   **Claude Code 전용**이다(Codex엔 정의 파일 기반 서브에이전트가 없다). 배경 `docs/adr/0007`.

용어(능동/반응 발동, 탐색 위임 래퍼)는 `CONTEXT.md`.

## 모드

- **apply** (기본): 자동 트리거 블록을 넣거나 최신으로 갱신하고, Claude Code면 탐색 위임 래퍼도 놓는다.
- **remove**: 자동 트리거 블록·탐색 위임 래퍼·두 스킬 디렉터리를 제거한다 (사용자가 "제거/삭제/uninstall"이라 할 때).

## 1. 호스트 감지 — 어느 메모리 파일인가

자동 트리거는 **모든 프로젝트에 걸친** 리마인드이므로 감지된 호스트의 **전역** 메모리 파일을
대상으로 한다. 순서대로 판별하라:

1. **자기 경로** — 이 SKILL.md의 베이스 디렉터리 경로를 본다(호출 시 주입됨). 경로에
   - `…/.claude/skills/…` 포함 → **Claude Code** → 대상 `~/.claude/CLAUDE.md`
   - `…/.codex/skills/…` 포함 → **Codex** → 대상 `~/.codex/AGENTS.md`
2. **파일시스템 프로브**(경로가 애매하면) — `~/.claude/skills/setup-gemini-delegate` 와
   `~/.codex/skills/setup-gemini-delegate` 중 **어느 쪽이 이 스킬을 담고 있나**로 판별한다.
3. **여전히 모호하면**(둘 다 있거나 판별 불가) → **사용자에게 물어라**:
   "Claude Code(CLAUDE.md)와 Codex(AGENTS.md) 중 어디에 넣을까요?" 추측하지 마라.

`~`는 사용자 홈으로 확장한다(Windows는 `C:\Users\<user>`).

## 2. 자동 트리거 블록 — 정본(canonical)

메모리 파일에 넣는 정확한 블록. 마커 두 줄은 **그대로** 유지하라 — 멱등·갱신·제거가 이
마커로 동작한다.

```
<!-- gemini-delegate:begin — managed by /setup-gemini-delegate (수동 편집 시 재실행에서 덮어써짐) -->
- 대량 파일 탐색·요약, 로그/데이터 분석, 보일러플레이트 생성, 정형 반복 수정을 시작하기 직전에는 gemini-delegate 스킬로 위임 적합성을 먼저 검토한다.
<!-- gemini-delegate:end -->
```

## 3. 탐색 위임 래퍼 — Claude Code 전용

정본은 이 스킬 디렉터리의 `templates/Explore.md`다. **직접 작성하지 말고 읽어서 치환해 써라.**

- **대상**: `~/.claude/agents/Explore.md` (전역. 디렉터리가 없으면 만든다)
- **치환**: 템플릿의 `{{DELEGATE_PY}}` 자리에 `delegate.py`의 실제 절대경로를 박는다.
  이 SKILL.md의 베이스 디렉터리에서 형제 디렉터리를 보면 된다 —
  `<base>/../gemini-delegate/delegate.py`. 경로를 정규화해서(`..` 없이) 쓰고,
  존재를 한 번 확인하라. 없으면 쓰지 말고 "gemini-delegate 스킬이 안 깔림"을 고지하라.
- **호스트 분기**: Codex면 **쓰지 말고** "Codex는 정의 파일 기반 서브에이전트를 지원하지 않아
  탐색 위임 래퍼는 건너뜁니다"를 한 줄 보고한다. 자동 트리거만 적용된다.
- **소유 마커**: 우리가 쓰는 파일은 frontmatter 바로 **뒤** 본문 첫 줄에
  `<!-- gemini-delegate:managed … -->`를 둔다(템플릿에 이미 있다). frontmatter *앞*에 두면
  서브에이전트 인식이 깨지므로 순서를 바꾸지 마라.

## 4. apply 절차

1. 호스트를 감지한다(위 1절).
2. 대상 메모리 파일을 읽는다(없으면 새로 만든다).
3. `<!-- gemini-delegate:begin` … `gemini-delegate:end -->` 마커 블록을 찾는다.
   - **없으면**: 파일 끝에 빈 줄 하나 두고 2절 블록을 덧붙인다. → "추가함"
   - **있고 내용이 정본과 다르면**: 마커 사이(마커 두 줄 포함)를 정본 블록으로 교체한다. → "갱신함"
   - **있고 내용이 같으면**: 아무것도 쓰지 않는다. → "이미 최신"
4. **Claude Code라면** 탐색 위임 래퍼를 처리한다(3절). `~/.claude/agents/Explore.md`가
   - **없으면**: 치환한 템플릿을 쓴다. → "추가함"
   - **있고 `gemini-delegate:managed` 마커를 포함하면**: 치환한 템플릿으로 통째 교체한다. → "갱신함"
   - **있는데 마커가 없으면**: **절대 덮어쓰지 마라.** 사용자 소유 파일이다. 상황을 알리고
     물어라 — 덮어쓸지 / 다른 이름으로 놓을지 / 건너뛸지. 답을 받기 전엔 아무것도 쓰지 마라.
5. **쓰기 전에 고지하라**: 어느 파일에, 무엇을, 어떤 동작(추가/갱신/건너뜀)으로 넣을지
   한 번 보여준다. 블록 밖 사용자 내용은 절대 건드리지 마라 — 마커 사이만 관리 영역이다.

## 5. remove 절차

1. 호스트를 감지한다(위 1절).
2. 대상 메모리 파일에서 마커 블록(마커 두 줄 포함)을 지우고, 남는 연속 빈 줄을 하나로
   정리한다. 마커가 없으면 넘어간다.
3. **Claude Code라면** `~/.claude/agents/Explore.md`를 확인한다. `gemini-delegate:managed`
   마커가 있을 때만 지운다. 마커가 없으면 **남겨 두고** 그 사실을 보고한다(우리 파일이 아니다).
4. 스킬 디렉터리 둘을 지운다:
   - Claude Code: `~/.claude/skills/gemini-delegate`, `~/.claude/skills/setup-gemini-delegate`
   - Codex: `~/.codex/skills/gemini-delegate`, `~/.codex/skills/setup-gemini-delegate`
5. 무엇을(파일 블록 + 래퍼 + 어느 디렉터리) 지웠는지 한 줄로 보고한다.

`npx skills remove gemini-delegate`로 스킬 파일만 지울 수도 있으나, 그건 자동 트리거 블록도
탐색 위임 래퍼도 지우지 않는다 — 그 둘의 제거는 이 스킬의 remove가 담당한다.

## 6. 경계 — 하지 말 것

- 블록 마커 밖의 사용자 내용을 수정·재배치하지 마라.
- 마커 없는 `Explore.md`를 덮어쓰지 마라. 이름이 흔해서 사용자 소유일 가능성이 실재한다.
- 탐색 위임 래퍼 내용을 기억으로 재작성하지 마라. 반드시 `templates/Explore.md`를 읽어서 써라.
- 프로젝트별이 아니라 **전역** 파일을 대상으로 하라(자동 트리거·래퍼 모두 프로젝트 횡단).
- 감지가 모호하면 추측하지 말고 물어라.
