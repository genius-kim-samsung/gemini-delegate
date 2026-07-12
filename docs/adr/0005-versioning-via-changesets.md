# 버전 관리는 Changesets로 — Python 레포에 Node 툴체인을 들이더라도

이 레포는 Python(`delegate.py`) + markdown 스킬로만 이뤄져 있고 Node 툴체인이 없었다. 그럼에도
버전 관리를 **Changesets**(`@changesets/cli`)로 도입해 참고 레포(`mattpocock/skills`)와 같은
파이프라인을 갖춘다. 레포 전체를 **단일 비공개 패키지**(`private: true`, 루트 `package.json` 하나,
`version` 하나)로 보고, 두 스킬(`gemini-delegate`·`setup-gemini-delegate`)이 한 버전으로 함께
오른다 — `--skill '*'`로 묶음 설치되는 현 구조와 일치한다. changeset 조각을 쌓았다가
`changeset version`으로 소비해 `CHANGELOG.md`를 갱신하고 버전을 범프하며, `changeset tag`로
`vX.Y.Z` 태그를 만든다. 실행은 CI 없이 **수동 로컬 3단계**다.

핵심 전제: 설치 CLI(`vercel-labs/skills`)는 버전 *문자열*을 읽지 않는다. 소비자 락파일
`.skill-lock.json`이 고정하는 것은 `ref`(브랜치/**태그**)와 스킬 폴더의 트리 SHA뿐이다. 즉 기계가
실제로 고정할 수 있는 유일한 손잡이는 **git 태그**이고(`owner/repo#v0.1.0`), `package.json`의 semver나
SKILL.md의 필드는 설치 도구가 소비하지 않는다. 따라서 Changesets가 만드는 산출물 중 **기계가 쓰는
부분은 git 태그**이며, `package.json`·`CHANGELOG.md`는 사람이 읽는 릴리스 위생이다. semver 등급은
**계약 기준**으로 정한다: major는 `delegate.py` CLI 계약·스킬 이름·검증 계약의 하위호환 파괴,
minor는 하위호환 신규, patch는 문구·버그픽스. 시작 버전은 `0.1.0`(공개 인터페이스가 아직 유동적 —
`docs/adr/0003`의 auto 라우팅 관측, `docs/adr/0002`의 agy 탈출구).

## Considered Options

- **경량 수동 — CHANGELOG를 손으로 쓰고 annotated git 태그만 (Node 없음)** — `Simplicity First`엔
  가장 부합하고 태그가 곧 소비자 핀 손잡이라 기능상 충분하다. 그러나 조각 누적·CHANGELOG 자동 생성이
  주는 이력 규율과 참고 레포 파이프라인 일치를 얻지 못한다. 기각.
- **태그만 (초경량, GitHub Releases 노트)** — 레포에 추가 파일 0. 대신 레포 내부에 변경 이력 파일이
  없어 오프라인에서 이력을 못 본다. 기각.
- **Changesets 완전 패리티 (채택)** — Node dev 의존성(`@changesets/cli`)이 루트에 들어오지만,
  이 툴링은 유지보수 전용이라 스킬 폴더에만 손대는 설치 CLI가 소비자에게 복사하지 않는다.
  참고 레포와 동일한 조각→버전→태그 흐름을 얻는다. 채택.
- **changelog 생성기: `@changesets/changelog-github` (mattpocock 동일)** — PR·작성자 링크가 붙지만
  `changeset version`마다 `GITHUB_TOKEN`·네트워크가 필요하고, 유지보수를 사외망(집)에서 직접
  커밋(PR 없음)하는 이 레포엔 이점이 없다. `@changesets/changelog-git`(커밋 기반, 오프라인 OK)을 채택.
- **스킬별 개별 버전 (multi-package)** — 두 스킬이 강결합돼 함께 설치·동작하므로 태그·CHANGELOG가
  2종으로 갈려 과하다. 기각.
