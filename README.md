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

- **위임 적합성은 난이도가 아니라 속성으로 판정.** spec 완결성, 검증 비용 ≪ 수행 비용,
  재시도 저렴, 보안 무관. 네 가지를 모두 만족할 때만 위임.
- **권한은 플래그로 기계적 강제.** 읽기 위임은 `--approval-mode plan`(읽기 전용),
  쓰기 위임은 `auto_edit`(파일 수정만 자동 승인). LLM의 선의에 의존하지 않는다.
- **검증 생략 불가.** 읽기 결과는 `경로:줄번호` 근거 인용 강제 + 스팟체크,
  쓰기 결과는 diff 검토.
- **출구 규칙.** 검증 탈락 시 피드백 담아 1회 재시도, 재탈락하면 오케스트레이터가
  직접 수행(회수). 워커 불능(쿼터 소진 등) 시 즉시 회수.
- **위임 장부.** 모든 위임을 `~/.claude/gemini-delegate/ledger.jsonl`에 기록.
  위임 기준 튜닝과 효과 판단의 근거.

## 설치

두 스킬로 구성: 위임 하네스 `gemini-delegate`와 설치 마무리용 `setup-gemini-delegate`.

**1. 스킬 설치**: 터미널에서 아래 명령어로 한 번에 설치한다.

```bash
npx skills@latest add genius-kim-samsung/gemini-delegate --skill '*' -g -y
```

`--skill '*'`는 두 스킬을 모두, `-g`는 전역(모든 프로젝트에서 발동), `-y`는 확인 프롬프트를
건너뛴다. 감지된 코딩 에이전트(Claude Code·Codex 등)의 전역 스킬 디렉터리에 설치된다.

**2. 자동 트리거 설정**: 에이전트에서 `/setup-gemini-delegate` 를 실행한다.
이 스킬이 AI 서비스를 감지해(Claude Code→`CLAUDE.md`, Codex→`AGENTS.md`) "작업 전 위임을
먼저 검토하라"는 자동 트리거를 전역 메모리 파일에 마커 블록으로 넣는다. **스킬 파일을 복사하는 것만으로는
능동적인 발동이 켜지지 않는다.** 이 한 줄이 긴 세션에서도 위임을 잊지 않게 한다(배경: `docs/adr/0004`).
`/gemini-delegate` 또는 "Gemini에게 시켜"로 명시 요청(반응 발동)은 이 자동 트리거 없이도 동작한다.

요구사항: Python 3.8+(위임 하네스 delegate.py 실행), **Gemini CLI**(사내 엔터프라이즈 워커, 설치·로그인).
gemini에 접근할 수 없는 사외망 개발/테스트 환경이라면 대신 agy를 쓸 수 있다.
아래 [사외망 개발/테스트](#사외망-개발테스트-agy) 참고.

## 삭제

에이전트에서 `/setup-gemini-delegate` 를 remove 모드로 실행한다(예: "gemini-delegate 제거").
AI 서비스를 감지해 메모리 파일의 자동 트리거 블록과 두 스킬 디렉터리를 함께 지운다. npx로 깔았다면
`npx skills remove gemini-delegate` 로 스킬 파일만 지울 수도 있으나, 그건 자동 트리거 블록을 남긴다.
블록은 마커(`<!-- gemini-delegate:begin/end -->`)로 찾아 지운다.

## 구성

```
skills/
├── gemini-delegate/
│   ├── SKILL.md      # 위임 판정 기준·spec 템플릿·검증/회수 규칙 (오케스트레이터가 읽음)
│   └── delegate.py   # 공용 코어: approval-mode 강제, 위임 계약 첨부, 타임아웃, 장부 기록
└── setup-gemini-delegate/
    └── SKILL.md      # 자동 트리거 문구를 AI 서비스 메모리 파일(CLAUDE.md/AGENTS.md)에 넣고/빼는 스킬
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

운영하면서 위임이 자주 회수되는 작업 유형이 보이면 `SKILL.md`의 카탈로그/네거티브
리스트에 반영하라. 판단 근거는 장부(`ledger.jsonl`)의 `result` 필드 분포를 보면 되고,
위임 1건당 오케스트레이터가 받은 출력량은 `output_chars`로 가늠할 수 있다.
