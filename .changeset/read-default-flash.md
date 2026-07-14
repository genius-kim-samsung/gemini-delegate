---
"gemini-delegate": minor
---

read 위임 기본 수행 모델을 auto에서 `gemini-3.5-flash`로 고정(`DEFAULT_READ_MODEL`, gemini 백엔드 전용). 저판단 read 위임까지 auto 라우터가 pro로 라우팅해 귀한 pro 쿼터가 새던 문제를 막는다. write 위임은 auto 유지 + 수행 모델 관측 지속, `--model` 오버라이드가 오면 우선. 전환 근거·배경은 ADR 0003 결정 갱신(2026-07-14).
