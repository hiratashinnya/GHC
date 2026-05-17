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
from typing import Any, Dict, Type, cast

EXIT_OK: int = 0
EXIT_BLOCK: int = 2


def _get_first(data: Dict, *keys: str, default: object = "") -> object:
    """Return the first present payload value among multiple key spellings."""
    for key in keys:
        if key in data:
            return data[key]
    return default


def _with_output_aliases(data: Dict[str, Any]) -> Dict[str, Any]:
    """Add snake_case aliases for hook output keys used by the runtime."""
    result = dict(data)

    if "systemMessage" in result and "system_message" not in result:
        result["system_message"] = result["systemMessage"]
    if "stopReason" in result and "stop_reason" not in result:
        result["stop_reason"] = result["stopReason"]

    hook_output = result.get("hookSpecificOutput")
    if isinstance(hook_output, dict):
        hook_specific_output = dict(hook_output)
        alias_pairs = {
            "hookEventName": "hook_event_name",
            "permissionDecision": "permission_decision",
            "permissionDecisionReason": "permission_decision_reason",
            "updatedInput": "updated_input",
            "additionalContext": "additional_context",
        }
        for camel_key, snake_key in alias_pairs.items():
            if camel_key in hook_specific_output and snake_key not in hook_specific_output:
                hook_specific_output[snake_key] = hook_specific_output[camel_key]
        result["hookSpecificOutput"] = hook_specific_output
        result.setdefault("hook_specific_output", hook_specific_output)

    return result


def _emit(data: Dict) -> None:
    """Write compact JSON to stdout (1 line, UTF-8)."""
    print(json.dumps(_with_output_aliases(data), ensure_ascii=False))


# ---------------------------------------------------------------------------
# stdin helper
# ---------------------------------------------------------------------------

_DECODE_CHAIN = ("utf-8", "cp932")


def read_payload() -> Dict:
    """Read the hook payload from stdin and return as a plain dict.

    Returns an empty dict when stdin is a TTY (manual / interactive run),
    on read error, or when the payload is not valid JSON.

    Decoding strategy (standard library only, no chardet):
    1. Try UTF-8 — VS Code hook runners always send UTF-8 bytes.
    2. Fall back to cp932 — Japanese Windows default locale.
    3. Last resort: UTF-8 with errors="replace" (payload may be garbled but
       never raises; the subsequent json.loads will likely fail and trigger the
       JSONDecodeError path).

    Errors are written to stderr so they surface as model context.
    """
    if sys.stdin.isatty():
        return {}
    try:
        raw_bytes = sys.stdin.buffer.read()
    except OSError as exc:
        print(f"[hook_payload] stdin read error: {exc}", file=sys.stderr)
        return {}
    if not raw_bytes:
        return {}

    raw: str = ""
    for enc in _DECODE_CHAIN:
        try:
            raw = raw_bytes.decode(enc).strip()
            break
        except UnicodeDecodeError:
            continue
    else:
        # All encodings failed — decode with replacement characters as last resort
        raw = raw_bytes.decode("utf-8", errors="replace").strip()
        print(
            f"[hook_payload] payload decoding failed for all encodings "
            f"{_DECODE_CHAIN}; decoded with replacement characters",
            file=sys.stderr,
        )

    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"[hook_payload] JSON parse error: {exc}", file=sys.stderr)
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
            "timestamp": _get_first(d, "timestamp", default=""),
            "cwd": _get_first(d, "cwd", default=""),
            "session_id": _get_first(d, "sessionId", "session_id", default=""),
            "hook_event_name": _get_first(d, "hookEventName", "hook_event_name", default=""),
            "transcript_path": _get_first(d, "transcript_path", "transcriptPath", default=""),
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "CommonPayload":
        return cls(**cls._common(d))

    # ------------------------------------------------------------------
    # Universal output methods (available on every event)
    # ------------------------------------------------------------------

    def block(self, stderr_message: str = "") -> int:
        """Block via exit code 2 — no stdout output.

        stderr_message is shown to the model as error context.
        Returns EXIT_BLOCK (2).
        """
        if stderr_message:
            print(stderr_message, file=sys.stderr)
        return EXIT_BLOCK

    def warn(self, message: str) -> int:
        """Show a warning in chat and continue (no block).

        Emits {"systemMessage": message}. Returns EXIT_OK (0).
        """
        _emit({"systemMessage": message})
        return EXIT_OK

    def stop_session(self, reason: str) -> int:
        """Stop the ENTIRE session. Use sparingly.

        Emits {"continue": false, "stopReason": reason}. Returns EXIT_OK (0).
        """
        _emit({"continue": False, "stopReason": reason})
        return EXIT_OK


# ---------------------------------------------------------------------------
# Mixin: context injection (PostToolUse, SessionStart, SubagentStart)
# ---------------------------------------------------------------------------

class _ContextMixin:
    """Mixin that adds add_context() to payload classes that support it.

    PostToolUse, SessionStart, and SubagentStart all share the same
    hookSpecificOutput.additionalContext output format.
    """

    hook_event_name: str  # declared for type checkers; provided by CommonPayload

    def add_context(self, text: str) -> int:
        """Inject additional context into the conversation.

        Emits hookSpecificOutput with additionalContext. Returns EXIT_OK (0).
        """
        _emit({
            "hookSpecificOutput": {
                "hookEventName": self.hook_event_name,
                "additionalContext": text,
            }
        })
        return EXIT_OK


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

    def deny(self, reason: str) -> int:
        """PreToolUse: block via permissionDecision deny.

        Preferred over block() when a user-visible reason is needed.
        Emits hookSpecificOutput with permissionDecision:"deny". Returns EXIT_OK (0).
        """
        _emit({
            "hookSpecificOutput": {
                "hookEventName": self.hook_event_name,
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        })
        return EXIT_OK

    def ask(self, reason: str) -> int:
        """PreToolUse: request user confirmation dialog (VS Code only).

        Emits hookSpecificOutput with permissionDecision:"ask". Returns EXIT_OK (0).
        """
        _emit({
            "hookSpecificOutput": {
                "hookEventName": self.hook_event_name,
                "permissionDecision": "ask",
                "permissionDecisionReason": reason,
            }
        })
        return EXIT_OK

    def update_input(self, new_input: Dict, context: str = "") -> int:
        """PreToolUse: replace tool inputs before execution.

        Emits hookSpecificOutput with updatedInput. Returns EXIT_OK (0).
        """
        hook_out: Dict = {
            "hookEventName": self.hook_event_name,
            "updatedInput": new_input,
        }
        if context:
            hook_out["additionalContext"] = context
        _emit({"hookSpecificOutput": hook_out})
        return EXIT_OK


@dataclass
class PostToolUsePayload(_ContextMixin, CommonPayload):
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

    def block_post(self, reason: str, context: str = "") -> int:
        """PostToolUse: block via top-level decision:block.

        Optionally injects additionalContext alongside the block.
        Returns EXIT_OK (0) — PostToolUse block uses exit 0 + JSON.
        """
        output: Dict = {"decision": "block", "reason": reason}
        if context:
            output["hookSpecificOutput"] = {
                "hookEventName": self.hook_event_name,
                "additionalContext": context,
            }
        _emit(output)
        return EXIT_OK


@dataclass
class UserPromptSubmitPayload(CommonPayload):
    """UserPromptSubmit — fires when the user sends a prompt."""

    prompt: str = ""

    @classmethod
    def from_dict(cls, d: Dict) -> "UserPromptSubmitPayload":
        return cls(**CommonPayload._common(d), prompt=d.get("prompt", ""))


@dataclass
class SessionStartPayload(_ContextMixin, CommonPayload):
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

    def block_stop(self, reason: str) -> int:
        """Stop: prevent the session from ending.

        Uses hookSpecificOutput wrapper (Stop event format).
        Returns EXIT_OK (0).
        """
        _emit({
            "hookSpecificOutput": {
                "hookEventName": self.hook_event_name,
                "decision": "block",
                "reason": reason,
            }
        })
        return EXIT_OK


@dataclass
class SubagentStartPayload(_ContextMixin, CommonPayload):
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

    def block_subagent(self, reason: str) -> int:
        """SubagentStop: prevent the subagent from completing.

        Top-level decision/reason format (no hookSpecificOutput wrapper).
        Returns EXIT_OK (0).
        """
        _emit({"decision": "block", "reason": reason})
        return EXIT_OK


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
    event_name = cast(str, _get_first(d, "hookEventName", "hook_event_name", default=""))
    cls = _DISPATCH.get(event_name, CommonPayload)
    return cls.from_dict(d)
