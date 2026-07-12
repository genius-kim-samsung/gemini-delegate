#!/usr/bin/env python3
"""gemini-delegate 스킬을 ~/.claude/skills/에 설치한다. 재실행하면 덮어쓴다."""

import shutil
import sys
from pathlib import Path

for stream in (sys.stdout, sys.stderr):
    stream.reconfigure(encoding="utf-8")

src = Path(__file__).parent / "skills" / "gemini-delegate"
dst = Path.home() / ".claude" / "skills" / "gemini-delegate"

if not shutil.which("gemini"):
    print("경고: gemini CLI가 PATH에 없습니다. 먼저 Gemini CLI를 설치·로그인하세요.", file=sys.stderr)

dst.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(src, dst, dirs_exist_ok=True)
print(f"설치 완료: {dst}")
print("\n권장: ~/.claude/CLAUDE.md에 아래 한 줄을 추가하면 긴 세션에서도 위임을 잊지 않습니다.")
print("  - 대량 탐색·요약·보일러플레이트·정형 반복 수정 전에는 gemini-delegate 스킬로 위임 적합성을 먼저 검토한다.")
