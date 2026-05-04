#!/usr/bin/env python3
"""PostToolUse hook: update docs/dashboard.md after tool execution.

Dispatches to patch_dashboard.py (D-3).  Only write-tools that touch a
docs/*.md file trigger an update; all other tools are skipped immediately.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

from debug_logging import HookDebugLogger
from hook_output import HookOutput
from hook_payload import read_payload
from tool_input import is_write_tool, get_written_paths

SCRIPT_DIR = Path(__file__).resolve().parent
PATCH_TIMEOUT_SECONDS = 30
DEBUG = HookDebugLogger(SCRIPT_DIR, "post_tool_dashboard_sync")


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------

def _extract_changed_file(payload: Dict, workspace_path: Path) -> Optional[str]:
    """Return the written file path when the triggering tool is a write-tool.

    Logs tool_input keys for debugging.  Returns None for non-write tools
    (caller should skip) and also None when the tool_input has no path key
    (caller falls back to full rebuild).
    """
    tool_name: str = payload.get("tool_name") or ""
    tool_input: Dict = payload.get("tool_input") or {}
    DEBUG.log("tool_input_keys", tool_name=tool_name, keys=list(tool_input.keys()))
    if tool_name and not is_write_tool(tool_name):
        DEBUG.log("skip", reason="non-write tool", tool_name=tool_name)
        return None
    paths = get_written_paths(tool_name, tool_input)
    return paths[0] if paths else None


def _is_non_write_tool(payload: Dict) -> bool:
    tool_name: str = payload.get("tool_name") or ""
    return bool(tool_name) and not is_write_tool(tool_name)


def _is_docs_md(changed_file: str, workspace_path: Path) -> bool:
    """Return True iff changed_file is under docs/ and ends with .md."""
    p = Path(changed_file) if os.path.isabs(changed_file) else workspace_path / changed_file
    try:
        p.resolve().relative_to((workspace_path / "docs").resolve())
        return p.suffix.lower() == ".md"
    except ValueError:
        return False


def _build_patch_cmd(patch_script: Path, changed_file: Optional[str], workspace_path: Path) -> List[str]:
    """Build the patch_dashboard.py command list."""
    cmd = [
        sys.executable, str(patch_script),
        "--docs-dir", "docs",
        "--dashboard", "docs/dashboard.md",
    ]
    if changed_file:
        try:
            rel = str(Path(changed_file).resolve().relative_to(workspace_path.resolve()))
        except ValueError:
            rel = changed_file
        cmd += ["--changed-file", rel]
    return cmd


def _run_patch(cmd: List[str], workspace: str, cmd_preview: str, out: HookOutput) -> subprocess.CompletedProcess:
    """Run patch_dashboard.py; return CompletedProcess or raise SystemExit on error."""
    try:
        result = subprocess.run(
            cmd, cwd=workspace, check=False,
            capture_output=True, text=True, encoding="utf-8",
            timeout=PATCH_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        DEBUG.log("error", cmd=cmd_preview, timeout_seconds=PATCH_TIMEOUT_SECONDS)
        sys.exit(out.warn(
            f"Dashboard sync hook timed out. cwd={workspace}; cmd={cmd_preview}; "
            f"timeout={PATCH_TIMEOUT_SECONDS}s"
        ))
    except OSError as exc:
        DEBUG.log("error", cmd=cmd_preview, exc=str(exc))
        sys.exit(out.warn(
            f"Dashboard sync hook failed to launch: {exc}; cwd={workspace}; cmd={cmd_preview}"
        ))
    DEBUG.log("done", returncode=result.returncode,
              stdout=result.stdout[-1000:], stderr=result.stderr[-1000:])
    return result


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    payload = read_payload()
    OUT = HookOutput(payload.get("hookEventName") or "PostToolUse")
    workspace = payload.get("cwd") or os.getcwd()
    workspace_path = Path(workspace)
    patch_script = workspace_path / ".github" / "scripts" / "patch_dashboard.py"

    DEBUG.log("input", tool_name=payload.get("tool_name"), cwd=workspace)

    # Skip read-only tools immediately
    if _is_non_write_tool(payload):
        return

    changed_file = _extract_changed_file(payload, workspace_path)

    # Skip writes to files outside docs/*.md
    if changed_file and not _is_docs_md(changed_file, workspace_path):
        DEBUG.log("skip", reason="not a docs/ .md file", changed_file=changed_file)
        return

    cmd = _build_patch_cmd(patch_script, changed_file, workspace_path)
    cmd_preview = " ".join(cmd)
    DEBUG.log("start", cwd=workspace, tool_name=payload.get("tool_name"),
              changed_file=changed_file, cmd=cmd_preview)

    if not patch_script.is_file():
        sys.exit(OUT.warn(
            f"Dashboard sync hook could not find patch script. cwd={workspace}; cmd={cmd_preview}"
        ))

    result = _run_patch(cmd, workspace, cmd_preview, OUT)

    if result.returncode == 0:
        return  # 何も出力しない（正常終了）
    else:
        sys.exit(OUT.warn(
            "Dashboard sync hook reported an error. "
            f"Check post_tool_dashboard_sync.debug.log. cwd={workspace}; cmd={cmd_preview}"
        ))


if __name__ == "__main__":
    main()
