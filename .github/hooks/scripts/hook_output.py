#!/usr/bin/env python3
"""hook_output.py — Output control helpers for VS Code Copilot hook scripts.

Each method emits JSON to stdout (when needed) and returns the appropriate
exit code. The caller is responsible for calling sys.exit(code).

Typical usage::

    from hook_output import HookOutput

    payload = _read_input() or {}
    OUT = HookOutput(payload.get("hookEventName", "PreToolUse"))

    # Block a tool:
    sys.exit(OUT.deny("本番ファイルへの直接書き込みは禁止されています"))

    # No action needed — just return, output nothing:
    return

Design notes
------------
* Silence is the default: return from main() without calling any method when
  no action is needed. Emitting {"continue": true} on every run pollutes the
  model context unnecessarily.
* Each method returns int (exit code). Use as sys.exit(OUT.method(...)).
* EXIT_OK / EXIT_BLOCK constants are exported for use in test assertions.
"""

from __future__ import annotations

import json
import sys
from typing import Dict

EXIT_OK: int = 0
EXIT_BLOCK: int = 2


def _emit(data: Dict) -> None:
    """Write compact JSON to stdout (1 line, UTF-8)."""
    print(json.dumps(data, ensure_ascii=False))


class HookOutput:
    """Output control for a single hook script invocation.

    Initialize once with the hookEventName from the incoming payload::

        OUT = HookOutput(payload.get("hookEventName", "PreToolUse"))
        sys.exit(OUT.deny("reason"))   # block
        # — or —
        return                         # no-op: output nothing
    """

    def __init__(self, event_name: str) -> None:
        self.event_name = event_name

    # ------------------------------------------------------------------
    # Universal patterns (any event)
    # ------------------------------------------------------------------

    def block(self, stderr_message: str = "") -> int:
        """Block via exit code 2 — simplest single-tool block.

        Nothing is written to stdout. stderr_message is shown to the model
        as error context. Returns EXIT_BLOCK (2).
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
        """Stop the ENTIRE session (not just one tool). Use sparingly.

        Emits {"continue": false, "stopReason": reason}. Returns EXIT_OK (0).
        """
        _emit({"continue": False, "stopReason": reason})
        return EXIT_OK

    # ------------------------------------------------------------------
    # PreToolUse patterns
    # ------------------------------------------------------------------

    def deny(self, reason: str) -> int:
        """PreToolUse: block via permissionDecision deny.

        Preferred over block() when a user-visible reason is needed.
        Emits hookSpecificOutput with permissionDecision:"deny". Returns EXIT_BLOCK (2).
        """
        _emit({
            "hookSpecificOutput": {
                "hookEventName": self.event_name,
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        })
        return EXIT_BLOCK

    def ask(self, reason: str) -> int:
        """PreToolUse: request user confirmation dialog (VS Code only).

        Emits hookSpecificOutput with permissionDecision:"ask". Returns EXIT_OK (0).
        """
        _emit({
            "hookSpecificOutput": {
                "hookEventName": self.event_name,
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
            "hookEventName": self.event_name,
            "updatedInput": new_input,
        }
        if context:
            hook_out["additionalContext"] = context
        _emit({"hookSpecificOutput": hook_out})
        return EXIT_OK

    # ------------------------------------------------------------------
    # PostToolUse patterns
    # ------------------------------------------------------------------

    def block_post(self, reason: str, context: str = "") -> int:
        """PostToolUse: block via top-level decision:block.

        Optionally injects additionalContext alongside the block.
        Returns EXIT_OK (0) — PostToolUse block uses exit 0 + JSON output.
        """
        output: Dict = {"decision": "block", "reason": reason}
        if context:
            output["hookSpecificOutput"] = {
                "hookEventName": self.event_name,
                "additionalContext": context,
            }
        _emit(output)
        return EXIT_OK

    # ------------------------------------------------------------------
    # Context injection (PostToolUse, SessionStart, SubagentStart)
    # ------------------------------------------------------------------

    def add_context(self, text: str) -> int:
        """Inject additional context into the conversation.

        Emits hookSpecificOutput with additionalContext. Returns EXIT_OK (0).
        """
        _emit({
            "hookSpecificOutput": {
                "hookEventName": self.event_name,
                "additionalContext": text,
            }
        })
        return EXIT_OK

    # ------------------------------------------------------------------
    # Stop event: prevent session from ending
    # ------------------------------------------------------------------

    def block_stop(self, reason: str) -> int:
        """Stop event: prevent the session from ending.

        Uses hookSpecificOutput wrapper (Stop event pattern).
        For SubagentStop, use block_post() instead (top-level decision).
        Returns EXIT_OK (0).
        """
        _emit({
            "hookSpecificOutput": {
                "hookEventName": self.event_name,
                "decision": "block",
                "reason": reason,
            }
        })
        return EXIT_OK
