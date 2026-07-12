#!/usr/bin/env python3
"""Gemini CLI 위임 공용 코어.

오케스트레이터(Claude Code/Codex)가 위임 적합한 하위 작업을 워커(Gemini CLI)에
넘길 때 사용한다. 위임 유형에 따라 --approval-mode를 기계적으로 강제하고,
위임 계약(근거 인용 등)을 spec에 자동 첨부하며, 모든 위임을 장부에 기록한다.

사용 예:
  python delegate.py --type read  "src/ 아래 인증 관련 모듈을 찾아 구조를 요약하라"
  python delegate.py --type write --spec-file spec.md
  echo "긴 spec..." | python delegate.py --type read
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

LEDGER_PATH = Path.home() / ".claude" / "gemini-delegate" / "ledger.jsonl"

# 위임 유형 → (gemini --approval-mode, spec에 첨부하는 위임 계약)
CONTRACTS = {
    "read": (
        "plan",
        "\n\n---\n[위임 계약 — 반드시 준수]\n"
        "- 모든 주장·발견에 근거를 `경로:줄번호` 형식으로 인용하라. "
        "근거를 제시할 수 없는 내용은 '미확인'으로 명시하라.\n"
        "- 직접 읽지 않은 내용을 사실처럼 쓰지 마라. 추측은 추측이라고 표시하라.\n"
        "- 파일을 수정하지 마라. 요청된 출력 형식만 담아 간결하게 반환하라.",
    ),
    "write": (
        "auto_edit",
        "\n\n---\n[위임 계약 — 반드시 준수]\n"
        "- 지시된 파일만 수정하라. 지시 밖 파일의 수정·생성·삭제 금지.\n"
        "- 판단이 필요한 모호한 지점을 만나면 임의로 결정하지 말고, "
        "아무것도 수정하지 않은 채 질문 목록만 반환하라.\n"
        "- 완료 후 수정한 파일 목록과 파일별 변경 요지를 반환하라.",
    ),
}


def read_spec(args):
    if args.spec and args.spec_file:
        sys.exit("오류: spec 인자와 --spec-file은 동시에 쓸 수 없습니다.")
    if args.spec:
        return args.spec
    if args.spec_file:
        return Path(args.spec_file).read_text(encoding="utf-8")
    data = sys.stdin.read()
    if not data.strip():
        sys.exit("오류: spec이 비었습니다. 인자, --spec-file, stdin 중 하나로 전달하세요.")
    return data


def append_ledger(row):
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Gemini CLI에 하위 작업을 위임한다.")
    parser.add_argument("spec", nargs="?", help="위임 지시문 (미지정 시 --spec-file 또는 stdin)")
    parser.add_argument("--spec-file", help="위임 지시문 파일 경로")
    parser.add_argument("--type", choices=("read", "write"), default="read",
                        help="위임 유형. read=읽기 전용 강제, write=파일 수정만 허용 (기본: read)")
    parser.add_argument("--model", help="gemini -m 오버라이드 (기본: CLI 기본 모델)")
    parser.add_argument("--timeout", type=int, default=600, help="초 단위 타임아웃 (기본: 600)")
    parser.add_argument("--retry", action="store_true", help="재시도 위임임을 장부에 표시")
    parser.add_argument("--dry-run", action="store_true", help="실행 없이 명령과 최종 spec만 출력")
    args = parser.parse_args()

    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")

    gemini = shutil.which("gemini")
    if not gemini:
        sys.exit("오류: gemini CLI를 PATH에서 찾을 수 없습니다.")

    approval_mode, contract = CONTRACTS[args.type]
    spec = read_spec(args).rstrip()
    full_spec = spec + contract

    cmd = [gemini, "-p", "stdin으로 전달된 위임 지시를 수행하라.",
           "--approval-mode", approval_mode, "--skip-trust"]
    if args.model:
        cmd += ["-m", args.model]

    if args.dry_run:
        print("명령:", subprocess.list2cmdline(cmd))
        print("--- 최종 spec (stdin으로 전달) ---")
        print(full_spec)
        return

    start = time.monotonic()
    try:
        proc = subprocess.run(cmd, input=full_spec, capture_output=True,
                              text=True, encoding="utf-8", timeout=args.timeout)
        result = "ok" if proc.returncode == 0 else "error"
        stdout, stderr, rc = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as e:
        result, rc = "timeout", 124
        stdout = (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = f"타임아웃: {args.timeout}초 초과"

    duration = round(time.monotonic() - start, 1)
    append_ledger({
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "type": args.type,
        "model": args.model or "default",
        "spec_summary": re.sub(r"\s+", " ", spec)[:120],
        "result": result,
        "duration_s": duration,
        "retry": args.retry,
    })

    if stdout:
        print(stdout, end="")
    if result != "ok":
        tail = "\n".join(stderr.strip().splitlines()[-15:])
        print(f"\n[delegate] 위임 {result} (rc={rc}, {duration}s)\n{tail}", file=sys.stderr)
    sys.exit(rc)


if __name__ == "__main__":
    main()
