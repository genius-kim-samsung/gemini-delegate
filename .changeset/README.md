# Changesets

이 폴더는 `@changesets/cli`가 관리한다. 이 레포는 **단일 패키지**(`gemini-delegate`,
두 스킬 묶음)로 버전을 매긴다. changeset 도구 문서는
[changesets 저장소](https://github.com/changesets/changesets)를 참고.

## semver 등급 (이 레포의 계약 기준)

changeset 조각을 만들 때 등급은 **계약 기준**으로 고른다:

- **major** — `delegate.py` CLI 계약 파괴(플래그 제거·이름변경·동작변경), 스킬 제거·이름변경,
  또는 SKILL.md 위임·검증 계약의 하위호환 깨짐.
- **minor** — 하위호환되는 신규(새 백엔드, 새 위임 카탈로그 항목, 새 플래그 등).
- **patch** — SKILL.md 문구 다듬기, 문서·오타, `delegate.py` 버그픽스(인터페이스 불변).

0.x 동안은 관례상 breaking도 minor로 흡수된다. 배경은 `docs/adr/0005`.

## 릴리스 흐름 (수동, 로컬)

```bash
# 변경할 때마다
npx changeset            # 조각 생성(등급·설명 입력) → .changeset/<name>.md 커밋

# 릴리스할 때
npx changeset version    # 조각 소비 → package.json 범프 + CHANGELOG.md 갱신
git commit -am "release: vX.Y.Z"
npx changeset tag        # vX.Y.Z 태그 생성
git push --follow-tags
```
