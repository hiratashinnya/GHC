#!/usr/bin/env python3
"""hook_payload.py — Payload parsing helpers for VS Code Copilot hook scripts.

Provides structured dataclasses for all 8 hook event types, plus helpers
for reading stdin and dispatching to the correct class.

Typical usage::

    from hook_payload import read_payload, parse_payload, PreToolUsePayload

    raw = read_payload()
    event = parse_payload(raw)
    if isinstance(event, PreToolUsePayload):
        print(event.tool_name, event.tool_input)

All dataclass fields have default values so missing payload keys never raise
KeyError — callers can safely access any field without extra guards.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, Type


# ---------------------------------------------------------------------------
# stdin helper
# ---------------------------------------------------------------------------

def read_payload() -> Dict:
    """Read the hook payload from stdin and return as a plain dict.

    Returns an empty dict when stdin is a TTY (manual / interactive run),
    on read error, or when the payload is not valid JSON.

    Reads via sys.stdin.buffer to ensure UTF-8 decoding regardless of the
    platform default encoding (e.g. cp932 on Japanese Windows). VS Code hook
    runners always send the payload as UTF-8 bytes; reading through the text
    layer with a non-UTF-8 locale would introduce surrogate-escaped characters
    that later cause UnicodeEncodeError when writing to log files.
    """
    if sys.stdin.isatty():
        return {}
    try:
        raw = sys.stdin.buffer.read().decode("utf-8").strip()
    except OSError:
        return {}
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


# ---------------------------------------------------------------------------
# Base dataclass
# ---------------------------------------------------------------------------

@dataclass
class CommonPayload:
    """Fields present in every hook event payload (camelCase → snake_case)."""

    timestamp: str = ""
    cwd: str = ""
    session_id: str = ""
    hook_event_name: str = ""
    transcript_path: str = ""

    @classmethod
    def _common(cls, d: Dict) -> Dict:
        """Extract common fields from a raw payload dict."""
        return {
            "timestamp": d.get("timestamp", ""),
            "cwd": d.get("cwd", ""),
            "session_id": d.get("sessionId", ""),
            "hook_event_name": d.get("hookEventName", ""),
            "transcript_path": d.get("transcript_path", ""),
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "CommonPayload":
        return cls(**cls._common(d))


# ---------------------------------------------------------------------------
# Event-specific subclasses
# ---------------------------------------------------------------------------

@dataclass
class PreToolUsePayload(CommonPayload):
    """PreToolUse — fires immediately before a tool call."""

    tool_name: str = ""
    tool_input: Dict = field(default_factory=dict)
    tool_use_id: str = ""

    @classmethod
    def from_dict(cls, d: Dict) -> "PreToolUsePayload":
        return cls(
            **CommonPayload._common(d),
            tool_name=d.get("tool_name", ""),
            tool_input=d.get("tool_input") or {},
            tool_use_id=d.get("tool_use_id", ""),
        )


@dataclass
class PostToolUsePayload(CommonPayload):
    """PostToolUse — fires immediately after a tool call completes."""

    tool_name: str = ""
    tool_input: Dict = field(default_factory=dict)
    tool_use_id: str = ""
    tool_response: Any = None

    @classmethod
    def from_dict(cls, d: Dict) -> "PostToolUsePayload":
        return cls(
            **CommonPayload._common(d),
            tool_name=d.get("tool_name", ""),
            tool_input=d.get("tool_input") or {},
            tool_use_id=d.get("tool_use_id", ""),
            tool_response=d.get("tool_response"),
        )


@dataclass
class UserPromptSubmitPayload(CommonPayload):
    """UserPromptSubmit — fires when the user sends a prompt."""

    prompt: str = ""

    @classmethod
    def from_dict(cls, d: Dict) -> "UserPromptSubmitPayload":
        return cls(**CommonPayload._common(d), prompt=d.get("prompt", ""))


@dataclass
class SessionStartPayload(CommonPayload):
    """SessionStart — fires when a new agent session begins."""

    source: str = ""

    @classmethod
    def from_dict(cls, d: Dict) -> "SessionStartPayload":
        return cls(**CommonPayload._common(d), source=d.get("source", ""))


@dataclass
class StopPayload(CommonPayload):
    """Stop — fires just before the agent session ends."""

    stop_hook_active: bool = False

    @classmethod
    def from_dict(cls, d: Dict) -> "StopPayload":
        return cls(
            **CommonPayload._common(d),
            stop_hook_active=bool(d.get("stop_hook_active", False)),
        )


@dataclass
class SubagentStartPayload(CommonPayload):
    """SubagentStart — fires when a subagent is launched."""

    agent_id: str = ""
    agent_type: str = ""

    @classmethod
    def from_dict(cls, d: Dict) -> "SubagentStartPayload":
        return cls(
            **CommonPayload._common(d),
            agent_id=d.get("agent_id", ""),
            agent_type=d.get("agent_type", ""),
        )


@dataclass
class SubagentStopPayload(CommonPayload):
    """SubagentStop — fires when a subagent completes."""

    agent_id: str = ""
    agent_type: str = ""
    stop_hook_active: bool = False

    @classmethod
    def from_dict(cls, d: Dict) -> "SubagentStopPayload":
        return cls(
            **CommonPayload._common(d),
            agent_id=d.get("agent_id", ""),
            agent_type=d.get("agent_type", ""),
            stop_hook_active=bool(d.get("stop_hook_active", False)),
        )


@dataclass
class PreCompactPayload(CommonPayload):
    """PreCompact — fires just before context compaction."""

    trigger: str = ""

    @classmethod
    def from_dict(cls, d: Dict) -> "PreCompactPayload":
        return cls(**CommonPayload._common(d), trigger=d.get("trigger", ""))


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_DISPATCH: Dict[str, Type[CommonPayload]] = {
    "PreToolUse": PreToolUsePayload,
    "PostToolUse": PostToolUsePayload,
    "UserPromptSubmit": UserPromptSubmitPayload,
    "SessionStart": SessionStartPayload,
    "Stop": StopPayload,
    "SubagentStart": SubagentStartPayload,
    "SubagentStop": SubagentStopPayload,
    "PreCompact": PreCompactPayload,
}


def parse_payload(d: Dict) -> CommonPayload:
    """Dispatch a raw payload dict to the appropriate typed dataclass.

    Falls back to CommonPayload for unknown or missing hookEventName values.
    """
    event_name = d.get("hookEventName", "")
    cls = _DISPATCH.get(event_name, CommonPayload)
    return cls.from_dict(d)
