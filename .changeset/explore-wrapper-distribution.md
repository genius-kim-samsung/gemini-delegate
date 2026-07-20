---
"gemini-delegate": minor
---

탐색 위임 래퍼(`Explore` 서브에이전트) 배포 추가. `/setup-gemini-delegate`가 Claude Code를 감지하면 `templates/Explore.md`의 `{{DELEGATE_PY}}`를 실제 설치 경로로 치환해 `~/.claude/agents/Explore.md`에 놓고, remove 시 `gemini-delegate:managed` 마커가 있을 때만 지운다. 마커 없는 동명 파일은 사용자 소유로 보고 손대지 않는다. Codex는 정의 파일 기반 서브에이전트가 없어 건너뛰며 그 사실을 고지한다. npx 채널이 서브에이전트를 배포하지 못하고 사내망에서 플러그인이 차단된 제약, 컨텍스트 격리를 얻지 못한다는 점은 ADR 0007에 기록.
