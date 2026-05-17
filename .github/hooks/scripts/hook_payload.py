#!/usr/bin/env python3
"""hook_payload.py — Facade for hook payload input, events, and output helpers."""

from __future__ import annotations

from typing import Optional, Type, TypeVar, cast

from hook_event import (
    CommonPayload,
    PostToolUsePayload,
    PreCompactPayload,
    PreToolUsePayload,
    SessionStartPayload,
    StopPayload,
    SubagentStartPayload,
    SubagentStopPayload,
    UserPromptSubmitPayload,
    parse_payload,
)
from hook_input import read_payload, HookDebugLogger
from hook_output import EXIT_BLOCK, EXIT_OK

PayloadType = TypeVar("PayloadType", bound=CommonPayload)


def get_hook_input(debug: Optional[HookDebugLogger] = None) -> CommonPayload:
    """Read stdin, parse the payload, and return a typed hook event."""
    return parse_payload(read_payload(debug=debug))


def get_hook_input_as(payload_type: Type[PayloadType], debug: Optional[HookDebugLogger] = None) -> PayloadType:
    """Read stdin and coerce the payload to a requested typed event class."""
    payload = read_payload(debug=debug)
    event = parse_payload(payload)
    if isinstance(event, payload_type):
        return event
    return cast(PayloadType, payload_type.from_dict(payload))

__all__ = [
    "EXIT_BLOCK",
    "EXIT_OK",
    "CommonPayload",
    "PreToolUsePayload",
    "PostToolUsePayload",
    "UserPromptSubmitPayload",
    "SessionStartPayload",
    "StopPayload",
    "SubagentStartPayload",
    "SubagentStopPayload",
    "PreCompactPayload",
    "read_payload",
    "parse_payload",
    "get_hook_input",
    "get_hook_input_as",
]
