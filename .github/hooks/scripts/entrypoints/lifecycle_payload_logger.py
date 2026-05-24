#!/usr/bin/env python3
"""Log lifecycle hook input payloads for session/subagent start and stop events."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = SCRIPT_DIR.parent
IMPORT_DIRS = (
    SCRIPTS_DIR / "core",
    SCRIPTS_DIR / "access_control",
    SCRIPTS_DIR / "tooling",
    SCRIPTS_DIR / "shared",
)
for import_dir in IMPORT_DIRS:
    if str(import_dir) not in sys.path:
        sys.path.insert(0, str(import_dir))

from debug_logging import HookDebugLogger
from hook_payload import parse_payload, read_payload

DEBUG = HookDebugLogger(SCRIPT_DIR, "lifecycle_payload_logger")
TARGET_EVENTS = {"SessionStart", "Stop", "SubagentStart", "SubagentStop"}


def _log_with_timestamp(message: str, **payload: object) -> None:
    timestamp = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    DEBUG.log(f"{timestamp} {message}", **payload)


def _serialize_payload(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, default=str)


def main() -> None:
    try:
        payload = read_payload()
        event = parse_payload(payload)
        if event.hook_event_name not in TARGET_EVENTS:
            _log_with_timestamp("skip", reason="non-target-event", event_name=event.hook_event_name)
            return

        _log_with_timestamp(
            "input_json",
            event_name=event.hook_event_name,
            payload=_serialize_payload(payload),
        )
        _log_with_timestamp("done", event_name=event.hook_event_name)
    except Exception as exc:
        _log_with_timestamp("error", exc=str(exc))


if __name__ == "__main__":
    main()
