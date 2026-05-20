#!/usr/bin/env python3
"""tool_input.py — Tool input schema helpers for VS Code Copilot hook scripts.

Provides constants and path-extraction helpers for classifying tools and
reading file paths from tool_input payloads.  Write-tool and read-tool
helpers are kept in one module because both are needed for access-control
decisions in PreToolUse hooks.

Typical usage::

    from tool_input import (
        is_write_tool, get_written_paths,
        is_read_tool, get_read_paths,
        get_command,
    )

    if is_write_tool(tool_name):
        for path in get_written_paths(tool_name, tool_input):
            ...  # gate check, audit log, etc.

    if is_read_tool(tool_name):
        for path in get_read_paths(tool_name, tool_input):
            ...  # read-access policy enforcement
"""

from __future__ import annotations

from typing import Dict, List


# ---------------------------------------------------------------------------
# Tool classification constants
# ---------------------------------------------------------------------------

WRITE_TOOLS: frozenset = frozenset({
    "replace_string_in_file",
    "create_file",
    "multi_replace_string_in_file",
})

READ_TOOLS: frozenset = frozenset({
    "read_file",
    "list_dir",
    "view_image",
})


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------

def is_write_tool(tool_name: str) -> bool:
    """Return True if the tool writes to the filesystem."""
    return tool_name in WRITE_TOOLS


def is_read_tool(tool_name: str) -> bool:
    """Return True if the tool reads from the filesystem."""
    return tool_name in READ_TOOLS


# ---------------------------------------------------------------------------
# Path extraction helpers
# ---------------------------------------------------------------------------

def get_written_paths(tool_name: str, tool_input: Dict) -> List[str]:
    """Return file paths written by a write tool.

    For ``multi_replace_string_in_file`` with multiple replacement entries,
    returns each distinct ``filePath`` from the ``replacements`` array.
    Falls back to the top-level ``filePath`` for single-file edits.

    Returns an empty list for non-write tools.
    """
    if tool_name == "multi_replace_string_in_file":
        replacements = tool_input.get("replacements") or []
        paths = [r.get("filePath", "") for r in replacements if r.get("filePath")]
        if not paths:
            fp = tool_input.get("filePath", "")
            if fp:
                paths = [fp]
        return paths

    if tool_name in ("replace_string_in_file", "create_file"):
        fp = tool_input.get("filePath", "")
        return [fp] if fp else []

    return []


def get_read_paths(tool_name: str, tool_input: Dict) -> List[str]:
    """Return file paths accessed by a read tool.

    * ``read_file`` / ``view_image`` → ``filePath``
    * ``list_dir`` → ``path``

    Returns an empty list for non-read tools.
    """
    if tool_name in ("read_file", "view_image"):
        fp = tool_input.get("filePath", "")
        return [fp] if fp else []

    if tool_name == "list_dir":
        p = tool_input.get("path", "")
        return [p] if p else []

    return []


# ---------------------------------------------------------------------------
# Per-tool input accessors
# ---------------------------------------------------------------------------

def get_command(tool_input: Dict) -> str:
    """Return the command string from a ``run_in_terminal`` tool_input."""
    return tool_input.get("command", "")
