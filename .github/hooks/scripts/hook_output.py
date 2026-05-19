#!/usr/bin/env python3
"""hook_output.py — Output helpers for VS Code Copilot hook scripts."""

from __future__ import annotations

import json
import sys
from typing import Any, Dict

EXIT_OK: int = 0
EXIT_BLOCK: int = 2


def _with_output_aliases(data: Dict[str, Any]) -> Dict[str, Any]:
    """Add snake_case aliases for hook output keys used by the runtime."""
    result = dict(data)

    if "systemMessage" in result and "system_message" not in result:
        result["system_message"] = result["systemMessage"]
    if "stopReason" in result and "stop_reason" not in result:
        result["stop_reason"] = result["stopReason"]

    if "hookSpecificOutput" in result and "hook_specific_output" not in result:
        hook_output = result["hookSpecificOutput"]
    elif "hook_specific_output" in result and "hookSpecificOutput" not in result:
        hook_output = result["hook_specific_output"]
    else:
        hook_output = None
    
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


def emit_output(data: Dict[str, Any]) -> None:
    """Write compact JSON to stdout (1 line, UTF-8)."""
    output = json.dumps(_with_output_aliases(data), ensure_ascii=False)
    sys.stdout.buffer.write(output.encode('utf-8') + b'\n')
