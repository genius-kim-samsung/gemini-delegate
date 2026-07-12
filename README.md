# gemini-delegate

Claude Code(또는 Codex CLI)의 **월별 토큰 한도를 아끼기 위한 위임 하네스**.

## 문제

사내 엔터프라이즈 환경에서 쓰는 AI CLI들의 토큰 정책이 다르다:

| CLI | 모델 성능 | 토큰 정책 |
|---|---|---|
| Claude Code / Codex CLI | 높음 | **월별 한도** — 아껴 써야 함 |
| Gemini CLI | 상대적으로 낮음 | **일일 초기화** — 사실상 넉넉함 |

그런데 고성능 세션이 소비하는 토큰의 상당 부분은 판단력이 필요 없는 작업(대량 파일
탐색·읽기, 로그 분석, 보일러플레이트)이다. 이 부분을 Gemini에 넘기면 고성능 토큰을
판단이 필요한 작업에만 쓸 수 있다.

## 원리 — 라우터가 아니라 위임

task 전체를 난이도 분류해서 CLI에 배정하는 방식(라우터)이 아니다. **오케스트레이터**
(Claude Code)가 작업 전체를 책임지고 수행하되, 작업 도중 위임 적합한 하위 작업만
**워커**(Gemini CLI)에 넘기고 결과를 검증해서 회수한다. 분류를 고성능 모델의 판단에
맡기므로 오분류 위험이 낮고, 잘못된 결과는 검증 단계에서 걸러진다.

핵심 설계:

- **위임 적합성은 난이도가 아니라 속성으로 판정** — spec 완결성, 검증 비용 ≪ 수행 비용,
  재시도 저렴, 보안 무관. 네 가지를 모두 만족할 때만 위임.
- **권한은 플래그로 기계적 강제** — 읽기 위임은 `--approval-mode plan`(읽기 전용),
  쓰기 위임은 `auto_edit`(파일 수정만 자동 승인). LLM의 선의에 의존하지 않는다.
- **검증 생략 불가** — 읽기 결과는 `경로:줄번호` 근거 인용 강제 + 스팟체크,
  쓰기 결과는 diff 검토.
- **출구 규칙** — 검증 탈락 시 피드백 담아 1회 재시도, 재탈락하면 오케스트레이터가
  직접 수행(회수). 워커 불능(쿼터 소진 등) 시 즉시 회수.
- **위임 장부** — 모든 위임을 `~/.claude/gemini-delegate/ledger.jsonl`에 기록.
  위임 기준 튜닝과 효과 판단의 근거.

## 설치

요구사항: Python 3.8+, Claude Code, 워커 CLI 1종 이상 —
사내망은 Gemini CLI(설치·로그인), 사외망은 agy(Antigravity CLI, 아래 [워커 백엔드](#워커-백엔드) 참고).

```bash
git clone <이 저장소>
cd gemini-delegate
python install.py
```

설치 후 Claude Code가 대량 탐색·보일러플레이트 작업 직전에 자동으로 위임을 검토한다.
`/delegate` 또는 "Gemini에게 시켜"로 명시적으로 시킬 수도 있다.

## 구성

```
skills/gemini-delegate/
├── SKILL.md      # 위임 판정 기준·spec 템플릿·검증/회수 규칙 (오케스트레이터가 읽음)
└── delegate.py   # 공용 코어: approval-mode 강제, 위임 계약 첨부, 타임아웃, 장부 기록
```

`delegate.py`는 호스트 무관 스크립트라 Codex CLI에서도 AGENTS.md에 사용법을 적어주면
그대로 쓸 수 있다 (읽기: `--type read`, 쓰기: `--type write`).

### 워커 백엔드

| 백엔드 | 대상 환경 | 권한 강제 플래그 |
|---|---|---|
| `gemini` (기본) | 사내 엔터프라이즈 Gemini CLI | `--approval-mode plan` / `auto_edit` |
| `agy` | 개인 환경(사외망). Gemini CLI 개인용 서비스는 2026-06-18 종료되어 Antigravity CLI로 대체됨 | `--mode plan` / `accept-edits` |

백엔드는 PATH 기준으로 자동 감지된다(gemini 우선, 없으면 agy). 강제하려면
`--backend gemini|agy`, 머신 단위로 고정하려면 환경변수 `GEMINI_DELEGATE_BACKEND=agy`
(gemini가 설치돼 있지만 인증이 안 되는 머신에서 유용). agy 설치:
`irm https://antigravity.google/cli/install.ps1 | iex` (Windows PowerShell),
최초 1회 `agy` 실행 후 Google 로그인 필요.

## 튜닝

운영하면서 위임이 자주 회수되는 작업 유형이 보이면 `SKILL.md`의 카탈로그/네거티브
리스트에 반영하라. 판단 근거는 장부(`ledger.jsonl`)의 `result` 필드 분포를 보면 되고,
위임 1건당 오케스트레이터가 받은 출력량은 `output_chars`로 가늠할 수 있다.
