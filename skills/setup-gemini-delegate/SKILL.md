---
name: setup-gemini-delegate
description: >-
  gemini-delegate 설치를 마무리하는 일회성 스킬. 자동 트리거("대량 작업 전 위임을
  먼저 검토하라")를 호스트 메모리 파일(Claude Code→CLAUDE.md, Codex→AGENTS.md)에
  마커 블록으로 넣거나 뺀다. 사용자가 "/setup-gemini-delegate", "위임 자동 트리거 설치",
  "gemini-delegate 설치 마무리", "gemini-delegate 제거/삭제"라고 할 때 발동한다.
  gemini-delegate 스킬을 새로 설치한 직후에도 실행한다.
---

# gemini-delegate 설치 마무리 (setup-gemini-delegate)

이 스킬은 **위임 하네스가 아니다.** gemini-delegate 스킬 파일을 복사하는 것
(`npx skills add`)은 파일만 놓을 뿐, 오케스트레이터가 대량 작업 전
**스스로** 위임을 검토하게 만드는 **능동 발동** 나사를 조이지 않는다. 그 나사가 호스트
메모리 파일에 들어가는 한 줄 자동 트리거다. 이 스킬이 그 자동 트리거를 넣고/뺀다.

배경·경계는 `docs/adr/0004`, 용어(능동/반응 발동)는 `CONTEXT.md`.

## 모드

- **apply** (기본): 자동 트리거 블록을 넣거나 최신으로 갱신한다.
- **remove**: 자동 트리거 블록과 두 스킬 디렉터리를 제거한다 (사용자가 "제거/삭제/uninstall"이라 할 때).

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

## 3. apply 절차

1. 대상 메모리 파일을 읽는다(없으면 새로 만든다).
2. `<!-- gemini-delegate:begin` … `gemini-delegate:end -->` 마커 블록을 찾는다.
   - **없으면**: 파일 끝에 빈 줄 하나 두고 위 블록을 덧붙인다. → "추가함"
   - **있고 내용이 정본과 다르면**: 마커 사이(마커 두 줄 포함)를 정본 블록으로 교체한다. → "갱신함"
   - **있고 내용이 같으면**: 아무것도 쓰지 않는다. → "이미 최신"
3. **쓰기 전에 고지하라**: 어느 파일에, 어떤 블록을, 어떤 동작(추가/갱신)으로 넣을지
   사용자에게 한 번 보여준다. 블록 밖 사용자 내용은 절대 건드리지 마라 — 마커 사이만 관리 영역이다.

## 4. remove 절차

1. 호스트를 감지한다(위 1절).
2. 대상 메모리 파일에서 마커 블록(마커 두 줄 포함)을 지우고, 남는 연속 빈 줄을 하나로
   정리한다. 마커가 없으면 넘어간다.
3. 스킬 디렉터리 둘을 지운다:
   - Claude Code: `~/.claude/skills/gemini-delegate`, `~/.claude/skills/setup-gemini-delegate`
   - Codex: `~/.codex/skills/gemini-delegate`, `~/.codex/skills/setup-gemini-delegate`
4. 무엇을(파일 블록 + 어느 디렉터리) 지웠는지 한 줄로 보고한다.

`npx skills remove gemini-delegate`로 스킬 파일만 지울 수도 있으나, 그건 자동 트리거 블록을 지우지
않는다 — 블록 제거는 이 스킬의 remove가 담당한다.

## 5. 경계 — 하지 말 것

- 블록 마커 밖의 사용자 내용을 수정·재배치하지 마라.
- 프로젝트별 메모리 파일이 아니라 **전역** 파일을 대상으로 하라(자동 트리거는 프로젝트 횡단).
- 감지가 모호하면 추측하지 말고 물어라.
