#!/usr/bin/env python3
"""hook_event.py — Typed hook event dataclasses and payload dispatch."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Type, cast

from hook_output import EXIT_BLOCK, EXIT_OK, emit_output
from tool_input_parser import get_write_paths, get_read_paths, get_command_string


def _get_first(data: Dict[str, Any], *keys: str, default: object = "") -> object:
    """Return the first present payload value among multiple key spellings."""
    for key in keys:
        if key in data:
            return data[key]
    return default


@dataclass
class CommonPayload:
    """Fields present in every hook event payload (camelCase → snake_case)."""

    timestamp: str = ""
    cwd: str = ""
    session_id: str = ""
    hook_event_name: str = ""
    transcript_path: str = ""

    @classmethod
    def _common(cls, data: Dict[str, Any]) -> Dict[str, object]:
        return {
            "timestamp": _get_first(data, "timestamp", default=""),
            "cwd": _get_first(data, "cwd", default=""),
            "session_id": _get_first(data, "sessionId", "session_id", default=""),
            "hook_event_name": _get_first(data, "hookEventName", "hook_event_name", default=""),
            "transcript_path": _get_first(data, "transcript_path", "transcriptPath", default=""),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CommonPayload":
        return cls(**cls._common(data))

    def block(self, stderr_message: str = "") -> int:
        if stderr_message:
            print(stderr_message, file=sys.stderr)
        return EXIT_BLOCK

    def warn(self, message: str) -> int:
        emit_output({"systemMessage": message})
        return EXIT_OK

    def stop_session(self, reason: str) -> int:
        emit_output({"continue": False, "stopReason": reason})
        return EXIT_OK


class _ContextMixin:
    """Mixin that adds add_context() to payload classes that support it."""

    hook_event_name: str

    def add_context(self, text: str) -> int:
        emit_output({
            "hookSpecificOutput": {
                "hookEventName": self.hook_event_name,
                "additionalContext": text,
            }
        })
        return EXIT_OK


@dataclass
class PreToolUsePayload(CommonPayload):
    tool_name: str = ""
    tool_input: Dict[str, Any] = field(default_factory=dict)
    tool_use_id: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PreToolUsePayload":
        return cls(
            **CommonPayload._common(data),
            tool_name=cast(str, data.get("tool_name", "")),
            tool_input=cast(Dict[str, Any], data.get("tool_input") or {}),
            tool_use_id=cast(str, data.get("tool_use_id", "")),
        )

    def deny(self, reason: str) -> int:
        emit_output({
            "hookSpecificOutput": {
                "hookEventName": self.hook_event_name,
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        })
        return EXIT_OK

    def ask(self, reason: str) -> int:
        emit_output({
            "hookSpecificOutput": {
                "hookEventName": self.hook_event_name,
                "permissionDecision": "ask",
                "permissionDecisionReason": reason,
            }
        })
        return EXIT_OK

    def update_input(self, new_input: Dict[str, Any], context: str = "") -> int:
        hook_output: Dict[str, Any] = {
            "hookEventName": self.hook_event_name,
            "updatedInput": new_input,
        }
        if context:
            hook_output["additionalContext"] = context
        emit_output({"hookSpecificOutput": hook_output})
        return EXIT_OK

    def write_paths(self) -> List[str]:
        """書き込み対象パスのリストを返す（tool_input_parser に委譲）。"""
        return get_write_paths(self.tool_name, self.tool_input)

    def read_paths(self) -> List[str]:
        """読み取り対象パスのリストを返す（tool_input_parser に委譲）。"""
        return get_read_paths(self.tool_name, self.tool_input)

    def command_string(self) -> str:
        """コマンド文字列を返す（tool_input_parser に委譲）。"""
        return get_command_string(self.tool_input)


@dataclass
class PostToolUsePayload(_ContextMixin, CommonPayload):
    tool_name: str = ""
    tool_input: Dict[str, Any] = field(default_factory=dict)
    tool_use_id: str = ""
    tool_response: Any = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PostToolUsePayload":
        return cls(
            **CommonPayload._common(data),
            tool_name=cast(str, data.get("tool_name", "")),
            tool_input=cast(Dict[str, Any], data.get("tool_input") or {}),
            tool_use_id=cast(str, data.get("tool_use_id", "")),
            tool_response=data.get("tool_response"),
        )

    def block_post(self, reason: str, context: str = "") -> int:
        output: Dict[str, Any] = {"decision": "block", "reason": reason}
        if context:
            output["hookSpecificOutput"] = {
                "hookEventName": self.hook_event_name,
                "additionalContext": context,
            }
        emit_output(output)
        return EXIT_OK


@dataclass
class UserPromptSubmitPayload(CommonPayload):
    prompt: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserPromptSubmitPayload":
        return cls(**CommonPayload._common(data), prompt=cast(str, data.get("prompt", "")))


@dataclass
class SessionStartPayload(_ContextMixin, CommonPayload):
    source: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionStartPayload":
        return cls(**CommonPayload._common(data), source=cast(str, data.get("source", "")))


@dataclass
class StopPayload(CommonPayload):
    stop_hook_active: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StopPayload":
        return cls(
            **CommonPayload._common(data),
            stop_hook_active=bool(data.get("stop_hook_active", False)),
        )

    def block_stop(self, reason: str) -> int:
        emit_output({
            "hookSpecificOutput": {
                "hookEventName": self.hook_event_name,
                "decision": "block",
                "reason": reason,
            }
        })
        return EXIT_OK


@dataclass
class SubagentStartPayload(_ContextMixin, CommonPayload):
    agent_id: str = ""
    agent_type: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SubagentStartPayload":
        return cls(
            **CommonPayload._common(data),
            agent_id=cast(str, data.get("agent_id", "")),
            agent_type=cast(str, data.get("agent_type", "")),
        )


@dataclass
class SubagentStopPayload(CommonPayload):
    agent_id: str = ""
    agent_type: str = ""
    stop_hook_active: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SubagentStopPayload":
        return cls(
            **CommonPayload._common(data),
            agent_id=cast(str, data.get("agent_id", "")),
            agent_type=cast(str, data.get("agent_type", "")),
            stop_hook_active=bool(data.get("stop_hook_active", False)),
        )

    def block_subagent(self, reason: str) -> int:
        emit_output({"decision": "block", "reason": reason})
        return EXIT_OK


@dataclass
class PreCompactPayload(CommonPayload):
    trigger: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PreCompactPayload":
        return cls(**CommonPayload._common(data), trigger=cast(str, data.get("trigger", "")))


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


def parse_payload(data: Dict[str, Any]) -> CommonPayload:
    """Dispatch a raw payload dict to the appropriate typed dataclass."""
    event_name = cast(str, _get_first(data, "hookEventName", "hook_event_name", default=""))
    payload_type = _DISPATCH.get(event_name, CommonPayload)
    return payload_type.from_dict(data)
