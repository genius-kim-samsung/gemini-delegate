# gemini-delegate

주로 활용하는 AI(Claude Code/Codex CLI)의 **토큰을 아끼기 위해** Gemini CLI에게 작업을 위임하는 하네스.

## 배경

사내 엔터프라이즈 환경에서 쓰는 AI CLI들의 토큰 정책이 다르다:

| CLI | 모델 성능 | 토큰 정책 |
|---|---|---|
| Claude Code / Codex CLI | 높음 | **월별 한도**(아껴 써야 함) |
| Gemini CLI | 상대적으로 낮음 | **일일 초기화**(사실상 넉넉함) |

그런데 고성능 세션이 소비하는 토큰의 상당 부분은 판단력이 필요 없는 작업(대량 파일
탐색·읽기, 로그 분석, 보일러플레이트)이다. 이 부분을 Gemini에 넘기면 고성능 토큰을
판단이 필요한 작업에만 쓸 수 있다.

## 원리: 라우터가 아니라 위임

Task 전체를 난이도 분류해서 CLI에 배정하는 방식(라우터)이 아니다. **오케스트레이터**
(Claude Code)가 작업 전체를 책임지고 수행하되, 작업 도중 위임 적합한 하위 작업만
**워커**(Gemini CLI)에 넘기고 결과를 검증해서 회수한다. 분류를 고성능 모델의 판단에
맡기므로 오분류 위험이 낮고, 잘못된 결과는 검증 단계에서 걸러진다.

핵심 설계:

- **위임 적합성은 난이도가 아니라 속성으로 판정.** 하드 게이트 둘(spec 완결성, 시크릿
  무관)은 예외 없이, 경제성 판단 둘(검증 비용 ≪ 수행 비용, 재시도 저렴)은 애매하면
  위임 쪽으로. 사용자가 명시 지시하면 경제성 판단은 오버라이드된다.
- **권한은 플래그로 기계적 강제.** 읽기 위임은 `--approval-mode plan`(읽기 전용),
  쓰기 위임은 `auto_edit`(파일 수정만 자동 승인). LLM의 선의에 의존하지 않는다.
- **검증 생략 불가.** 읽기 결과는 `경로:줄번호` 근거 인용 강제 + 스팟체크,
  쓰기 결과는 diff 검토.
- **출구 규칙.** 검증 탈락 시 피드백 담아 1회 재시도, 재탈락하면 오케스트레이터가
  직접 수행(회수). 워커 불능(쿼터 소진 등) 시 즉시 회수.
- **위임 장부.** 모든 위임과 회수를 `~/.claude/gemini-delegate/ledger.jsonl`에 기록.
  위임 기준 튜닝과 효과 판단의 근거.

## 설치

두 스킬로 구성: 위임 하네스 `gemini-delegate`와 설치 마무리용 `setup-gemini-delegate`.

**1. 스킬 설치**: 터미널에서 아래 명령어로 한 번에 설치한다.

```bash
npx skills@latest add genius-kim-samsung/gemini-delegate --skill '*' -g -y
```

`--skill '*'`는 두 스킬을 모두, `-g`는 전역(모든 프로젝트에서 발동), `-y`는 확인 프롬프트를
건너뛴다. 감지된 코딩 에이전트(Claude Code·Codex 등)의 전역 스킬 디렉터리에 설치된다.

특정 버전에 고정하려면 소스 뒤에 태그를 붙인다 — `...gemini-delegate#v0.1.0 --skill '*' -g -y`.
붙이지 않으면 최신 `main`을 받는다. 설치한 스킬 갱신은 `npx skills update` — **갱신 후에는
`/setup-gemini-delegate`를 다시 실행하라**(아래 2단계가 놓는 파일들은 복사본이라 자동으로
따라오지 않는다). 버전 목록과 변경 이력은 [`CHANGELOG.md`](CHANGELOG.md) 및 git 태그(`v*`)를 본다.

**2. 설치 마무리**: 에이전트에서 `/setup-gemini-delegate` 를 실행한다. **스킬 파일을 복사하는
것만으로는 능동적인 발동이 켜지지 않는다.** 이 스킬이 AI 서비스를 감지해 스킬 배포 채널이
건드리지 않는 두 자리를 채운다.

- **자동 트리거** — "작업 전 위임을 먼저 검토하라"는 한 줄을 전역 메모리 파일
  (Claude Code→`CLAUDE.md`, Codex→`AGENTS.md`)에 마커 블록으로 넣는다. 긴 세션에서도 위임을
  잊지 않게 한다(배경: `docs/adr/0004`).
- **탐색 위임 래퍼** — 탐색을 직접 하지 못하게 강제하는 `Explore` 서브에이전트를
  `~/.claude/agents/`에 놓는다. **Claude Code 전용**이며(Codex엔 대응 개념이 없어 건너뛴다),
  이미 같은 이름의 파일이 있으면 덮어쓰지 않고 물어본다(배경: `docs/adr/0007`).

`/gemini-delegate` 또는 "Gemini에게 시켜"로 명시 요청(반응 발동)은 이 2단계 없이도 동작한다.

요구사항: Python 3.8+(위임 하네스 delegate.py 실행), **Gemini CLI**(사내 엔터프라이즈 워커, 설치·로그인).
gemini에 접근할 수 없는 사외망 개발/테스트 환경이라면 대신 agy를 쓸 수 있다.
아래 [사외망 개발/테스트](#사외망-개발테스트-agy) 참고.

## 삭제

에이전트에서 `/setup-gemini-delegate` 를 remove 모드로 실행한다(예: "gemini-delegate 제거").
AI 서비스를 감지해 메모리 파일의 자동 트리거 블록, 탐색 위임 래퍼, 두 스킬 디렉터리를 함께 지운다.
npx로 깔았다면 `npx skills remove gemini-delegate` 로 스킬 파일만 지울 수도 있으나, 그건 앞의 둘을
남긴다. 우리가 놓은 것은 마커(`<!-- gemini-delegate:begin/end -->`,
`<!-- gemini-delegate:managed -->`)로 찾아 지우며, 마커 없는 파일은 손대지 않는다.

## 구성

```
skills/
├── gemini-delegate/
│   ├── SKILL.md      # 위임 판정 기준·spec 템플릿·검증/회수 규칙 (오케스트레이터가 읽음)
│   └── delegate.py   # 공용 코어: approval-mode 강제, 위임 계약 첨부, 타임아웃, 장부 기록
└── setup-gemini-delegate/
    ├── SKILL.md      # 자동 트리거 문구와 탐색 위임 래퍼를 넣고/빼는 스킬
    └── templates/
        └── Explore.md  # 탐색 위임 래퍼 정본 (Claude Code 서브에이전트, 설치 시 경로 치환)
```

`delegate.py`는 특정 AI 서비스에 종속되지 않은 스크립트라 Codex CLI에서도 AGENTS.md에 사용법을 적어주면
그대로 쓸 수 있다 (읽기: `--type read`, 쓰기: `--type write`).

### 워커 백엔드

정식 경로의 워커는 **Gemini CLI 하나**다(사내 엔터프라이즈). 위임 유형에 따라
권한이 플래그로 강제된다. 읽기 `--approval-mode plan`, 쓰기 `auto_edit`.
자동 감지도, 다른 백엔드로의 폴백도 없다. gemini 호출이 실패하면 오케스트레이터가
곧바로 회수(직접 수행)한다.

### 사외망 개발/테스트 (agy)

이 스킬은 사내망 전용이지만, 유지보수는 Gemini CLI에 접근할 수 없는 사외망에서 한다.
그 경우에만 워커를 Antigravity CLI(`agy`)로 대체해 테스트할 수 있다. **정식 경로가
아니라 개발 전용 탈출구다.** 배경은 [ADR 0002](docs/adr/0002-agy-dev-only-not-peer-backend.md) 참고.

- **스위치**: 개발 머신에 환경변수 `GEMINI_DELEGATE_DEV_AGY=1`을 설정하면 agy가 열린다.
  이 스위치가 없으면 `--backend agy`는 하드 에러로 거부되어, 정식 코드 경로에 agy가
  새어 들어가지 않는다.
- 스위치가 켜지면 기본 백엔드가 agy가 되므로 `--backend`를 따로 넘길 필요가 없다.
  (권한 강제: 읽기 `--mode plan`, 쓰기 `accept-edits`.)
- **agy 설치**: `irm https://antigravity.google/cli/install.ps1 | iex` (Windows PowerShell),
  최초 1회 `agy` 실행 후 Google 로그인. (Gemini CLI 개인용 서비스가 2026-06-18 종료되어
  개인 환경에서는 후속인 Antigravity CLI를 쓴다.)

## 튜닝

운영하면서 위임이 자주 회수되는 작업 유형이 보이면 `SKILL.md`의 카탈로그에 반영하라.
판단 근거는 장부(`ledger.jsonl`)다.

- **얼마나 실패하는가** — `result` 분포. `reclaimed-verify`(검증 재탈락)와
  `reclaimed-worker`(워커 불능)를 나눠 보면 완화된 판정 기준(속성 2·3)이 어디서
  깨지는지 드러난다. 재위임률은 `retry` 필드로 본다.
- **얼마나 아꼈는가** — `tokens`(워커가 대신 태운 토큰)와 `spec_chars`(그 대가로
  오케스트레이터가 쓴 spec 분량)를 함께 본다. `spec_chars`가 크고 `tokens`가 작은 위임이
  반복되면 그 유형은 위임 고정비가 이득을 먹고 있다는 뜻이다 — 카탈로그에서 내려라.
