# gemini-delegate

## 0.1.0

위임 하네스 최초 버전.

- 두 스킬 구성: `gemini-delegate`(위임 판정·검증·회수 하네스), `setup-gemini-delegate`(자동 트리거를 호스트 메모리 파일에 넣고/빼는 설치 마무리).
- 워커 백엔드는 gemini 하나(정식). agy는 `GEMINI_DELEGATE_DEV_AGY=1`이 켜진 사외망 개발 머신 전용 탈출구.
- 위임 유형별 권한을 플래그로 기계적 강제(읽기 `--approval-mode plan`, 쓰기 `auto_edit`).
- 검증 생략 불가(읽기: 근거 인용 + 스팟체크, 쓰기: diff 검토)와 출구 규칙(1회 재시도 후 회수).
- 위임 장부(`ledger.jsonl`) 기록, 수행 모델 관측(gemini `--output-format json`의 `stats.models`).
