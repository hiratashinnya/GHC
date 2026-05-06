#!/usr/bin/env python3
"""Debug spy hook: capture full tool_input payload for all tools.

Registers on both PreToolUse and PostToolUse to record every tool invocation.
Always returns {"continue": true} — never blocks execution.

Debug enable/disable
--------------------
ON  : create  .github/hooks/scripts/tool_input_spy.debug
OFF : delete  .github/hooks/scripts/tool_input_spy.debug

Log file : .github/hooks/scripts/tool_input_spy.debug.log
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict

from debug_logging import HookDebugLogger
from hook_payload import read_payload

SCRIPT_DIR = Path(__file__).resolve().parent
DEBUG = HookDebugLogger(SCRIPT_DIR, "tool_input_spy")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="tool_input spy hook")
    p.add_argument(
        "--event",
        choices=["PreToolUse", "PostToolUse"],
        default="PostToolUse",
        help="Hook event type (passed from hook config)",
    )
    return p.parse_args()


def _sanitize(value: object, max_len: int = 300) -> object:
    """Truncate long strings to keep the log readable."""
    if isinstance(value, str) and len(value) > max_len:
        return value[:max_len] + f"...[truncated {len(value) - max_len} chars]"
    if isinstance(value, dict):
        return {k: _sanitize(v, max_len) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize(v, max_len) for v in value]
    return value


def main() -> None:
    args = _parse_args()
    try:
        payload = read_payload()

        tool_name: str = payload.get("tool_name") or "(unknown)"
        tool_input: Dict = payload.get("tool_input") or {}
        tool_response: object = payload.get("tool_response")

        DEBUG.log(
            "input",
            event=args.event,
            tool_name=tool_name,
        )

        # Spy log with full tool_input and tool_response (if present).  Use a separate "spy" label to distinguish from the initial "input" log.
        DEBUG.log(
            "spy",
            event=args.event,
            tool_name=tool_name,
            tool_input=_sanitize(tool_input),
            **({} if tool_response is None else {"tool_response": _sanitize(tool_response)}),
            input_payload=payload,
        )
        DEBUG.log("done")
    except Exception as exc:
        DEBUG.log("error", exc=str(exc))


if __name__ == "__main__":
    main()
