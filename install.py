#!/usr/bin/env python3
"""gemini-delegate 스킬들을 ~/.claude/skills/에 복사한다. 재실행하면 덮어쓴다.

이 설치기는 스킬 파일 복사만 하는 오프라인·사내망 안전망이다. 온라인에서는
`npx skills add <owner>/gemini-delegate`로도 설치할 수 있다. 어느 경로로 설치했든,
능동 위임 넛지를 호스트 메모리 파일(CLAUDE.md/AGENTS.md)에 넣으려면 설치 후
에이전트에서 /setup-gemini-delegate 스킬을 실행하라 (배경: docs/adr/0004)."""

import os
import shutil
import sys
from pathlib import Path

for stream in (sys.stdout, sys.stderr):
    stream.reconfigure(encoding="utf-8")

src_root = Path(__file__).parent / "skills"
dst_root = Path.home() / ".claude" / "skills"

has_agy = shutil.which("agy") or (
    Path(os.environ.get("LOCALAPPDATA", "")) / "agy" / "bin" / "agy.exe").exists()
dev_agy = os.environ.get("GEMINI_DELEGATE_DEV_AGY", "").strip().lower() in (
    "1", "true", "yes", "on")

if not shutil.which("gemini"):
    print("경고: 정식 워커인 Gemini CLI가 없습니다. 사내망에서 설치·로그인하세요 (README 참고).",
          file=sys.stderr)
if dev_agy and not has_agy:
    print("경고: 개발 모드(GEMINI_DELEGATE_DEV_AGY=1)인데 agy가 없습니다. "
          "사외망 테스트용 agy를 설치·로그인하세요 (README 참고).", file=sys.stderr)

dst_root.mkdir(parents=True, exist_ok=True)
copied = []
for skill_dir in sorted(p for p in src_root.iterdir() if p.is_dir()):
    shutil.copytree(skill_dir, dst_root / skill_dir.name, dirs_exist_ok=True)
    copied.append(skill_dir.name)

print(f"설치 완료: {dst_root} — {', '.join(copied)}")
print("\n다음: 에이전트에서 /setup-gemini-delegate 를 실행하면 능동 위임 넛지를")
print("호스트 메모리 파일(CLAUDE.md/AGENTS.md)에 마커 블록으로 넣습니다.")
print("(스킬 파일 복사만으로는 능동 발동이 켜지지 않습니다 — docs/adr/0004.)")
