# gemini-delegate

Claude Code/Codex의 월별 토큰 한도를 아끼기 위한 위임 하네스. 오케스트레이터(고성능)가
작업을 수행하며 위임 적합한 하위 작업만 워커(Gemini CLI)에 넘기고 검증·회수한다.

배경·설계는 `README.md`, 용어(ubiquitous language)는 `CONTEXT.md`, 설계 결정은
`docs/adr/`를 읽어라. 아래는 **이 저장소 코드를 고칠 때** 필요한 것만 적는다.

## 네 갈래 산출물 — 헷갈리지 말 것

- **위임 스킬 지시문** `skills/gemini-delegate/SKILL.md` — 오케스트레이터가 읽는 위임 판정·검증 규칙.
- **하네스 코드** `skills/gemini-delegate/delegate.py` — 권한 강제·계약 첨부·장부 기록 스크립트(호스트 무관).
- **설치 마무리 스킬** `skills/setup-gemini-delegate/SKILL.md` — 자동 트리거와 탐색 위임 래퍼를 넣고/빼는 스킬. 에이전트가 실행하며 호스트를 감지한다(배경 `docs/adr/0004`).
- **탐색 위임 래퍼 정본** `skills/setup-gemini-delegate/templates/Explore.md` — setup이 경로 치환 후 `~/.claude/agents/`에 복사하는 Claude Code 서브에이전트. 이 파일이 **유일한 정본**이다(배경 `docs/adr/0007`).

## Commands

| Command | Description |
|---|---|
| `/setup-gemini-delegate` (에이전트에서) | 자동 트리거(메모리 파일)와 탐색 위임 래퍼(Claude Code 전용)를 넣음/제거(호스트 감지). |
| `python skills/gemini-delegate/delegate.py --dry-run --type read "spec"` | 실행 없이 최종 명령·spec만 확인. |
| dev 테스트 | `GEMINI_DELEGATE_DEV_AGY=1` 설정 후 `delegate.py`를 실행하면 agy 백엔드로 실제 위임(사외망). |
| 릴리스 | `npx changeset`(조각) → `npx changeset version`(범프+CHANGELOG) → `npx changeset tag` → `git push --follow-tags`. CI 없음, 수동. 배경 `docs/adr/0005`. |

## Gotchas

- **repo ≠ 설치본**: 편집은 repo에서, 실행은 `~/.claude/skills/`(또는 `~/.codex/skills/`)의 복사본에서 한다. `npx skills add` 로 다시 설치하기 전엔 스킬 변경이 먹지 않는다.
- **자동 트리거는 setup 스킬 단독 소유**: CLAUDE.md/AGENTS.md 마커 블록을 넣고 빼는 로직은 `setup-gemini-delegate` 스킬에만 있다. 배포 경계는 `docs/adr/0004`.
- **탐색 위임 래퍼는 Claude Code 전용 비대칭**: Codex엔 정의 파일 기반 서브에이전트가 없어 setup이 건너뛴다. 저장소에 `.claude/agents/Explore.md` 사본을 두지 마라(gitignore됨) — 정본은 `templates/Explore.md` 하나이고, 이원화되면 반드시 어긋난다. 격리 효용이 아니라 **강제·spec 대행**이 목적이라는 점을 문서가 과장하지 않게 하라. 배경 `docs/adr/0007`.
- **정식 백엔드는 gemini 하나** — 자동 감지·폴백 없음. agy는 `GEMINI_DELEGATE_DEV_AGY=1`이 켜진 사외망 개발 머신 전용 탈출구다(스위치 꺼지면 `--backend agy`는 하드 에러). 이 경계를 무너뜨리기 전에 `docs/adr/0002` 읽을 것.
- **용어를 지켜라**: 오케스트레이터/워커/위임/회수/수행 모델은 `CONTEXT.md`가 못박은 용어다. `_Avoid_` 목록의 단어(라우터·폴백·롤백 등)로 바꾸지 마라.
- **delegate.py는 호스트 무관**: Claude Code 전용 기능에 의존하지 마라 — Codex에서도 AGENTS.md로 그대로 쓴다.
- **read 위임 기본은 flash 고정(`DEFAULT_READ_MODEL`), write는 auto 유지**: 저판단 read 위임에 pro 쿼터가 새는 걸 막으려 read 기본 모델을 `gemini-3.5-flash`로 고정했다(전환 근거·배경 `docs/adr/0003`). write 위임은 여전히 auto 라우터에 맡기고 수행 모델을 장부로 관측한다. `--model`이 오면 우선하며, 모델 id가 바뀌면 상수 한 곳만 갱신하라.
- **버전 관리는 루트 Node 툴링(유지보수 전용)**: `package.json`·`.changeset/`는 루트에만 있고 스킬 폴더엔 없어 설치 CLI가 소비자에게 복사하지 않는다. 설치 도구는 버전 *문자열*을 안 읽고, 소비자 핀 손잡이는 **git 태그**뿐(`owner/repo#v0.1.0`). semver는 계약 기준(major=CLI·스킬명·검증 계약 파괴). 배경 `docs/adr/0005`. 레포=단일 비공개 패키지.
- 테스트 스위트 없음. `--dry-run`으로 명령을 확인하고, 사외망에선 agy로 실제 왕복해 검증한다. agy는 spec을 명령줄 인자로 받아 ~30,000자 한계(`AGY_SPEC_LIMIT`)가 있다.
