#!/usr/bin/env python3
"""<HookName> hook: <purpose>."""
from __future__ import annotations
from pathlib import Path
from debug_logging import HookDebugLogger
from hook_output import HookOutput
from hook_payload import read_payload, parse_payload, PreToolUsePayload
from tool_input import is_write_tool, get_written_paths, is_read_tool, get_read_paths

SCRIPT_DIR = Path(__file__).resolve().parent
DEBUG = HookDebugLogger(SCRIPT_DIR, "<script_name>")


def main() -> None:
    try:
        raw = read_payload()
        event = parse_payload(raw)
        OUT = HookOutput(event.hook_event_name or "PreToolUse")

        DEBUG.log("input", hook_event=event.hook_event_name)

        if isinstance(event, PreToolUsePayload):
            tool_name = event.tool_name
            tool_input = event.tool_input

            # 書き込みアクセス制御（必要な場合は tool_input のバリデーションも実装すること）
            if is_write_tool(tool_name):
                paths = get_written_paths(tool_name, tool_input)
                # 例: sys.exit(OUT.deny(f"書き込みをブロック: {paths}"))

            # 読み取りアクセス制御（必要な場合は tool_input のバリデーションも実装すること）
            if is_read_tool(tool_name):
                paths = get_read_paths(tool_name, tool_input)
                # 例: sys.exit(OUT.deny(f"読み取りをブロック: {paths}"))

        # 出力制御: sys.exit(OUT.method(...)) で行う。何もしない場合は return するだけ。
        # 例: sys.exit(OUT.deny("理由"))        # PreToolUse ブロック
        #     sys.exit(OUT.warn("警告"))         # 警告表示（続行）
        #     sys.exit(OUT.block("理由"))        # exit 2 のみのブロック
        #     sys.exit(OUT.stop_session("理由")) # セッション全体の停止

        DEBUG.log("done")
        # 何も出力しない（正常終了）
    except Exception as exc:
        DEBUG.log("error", exc=str(exc))


if __name__ == "__main__":
    main()
