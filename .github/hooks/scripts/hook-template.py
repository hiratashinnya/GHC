#!/usr/bin/env python3
"""<HookName> hook: <purpose>."""
from __future__ import annotations
import json, sys
from pathlib import Path
from typing import Dict, Optional
from debug_logging import HookDebugLogger
from hook_output import HookOutput

SCRIPT_DIR = Path(__file__).resolve().parent
DEBUG = HookDebugLogger(SCRIPT_DIR, "<script_name>")


def _read_input() -> Optional[Dict]:
    if sys.stdin.isatty():
        return None
    raw = sys.stdin.read().strip()
    return json.loads(raw) if raw else None


def main() -> None:
    payload = _read_input() or {}
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    OUT = HookOutput(payload.get("hookEventName", "PreToolUse"))

    DEBUG.log("input", tool_name=tool_name, keys=list(tool_input.keys()))

    # ... 処理 ...

    # 出力制御: sys.exit(OUT.method(...)) で行う。何もしない場合は return するだけ。
    # 例: sys.exit(OUT.deny("理由"))        # PreToolUse ブロック
    #     sys.exit(OUT.warn("警告"))         # 警告表示（続行）
    #     sys.exit(OUT.block("理由"))        # exit 2 のみのブロック
    #     sys.exit(OUT.stop_session("理由")) # セッション全体の停止

    DEBUG.log("done")
    # 何も出力しない（正常終了）


if __name__ == "__main__":
    main()
