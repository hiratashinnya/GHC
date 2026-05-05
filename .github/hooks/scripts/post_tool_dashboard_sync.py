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
from typing import List, Optional

from debug_logging import HookDebugLogger
from hook_output import HookOutput
from hook_payload import read_payload, parse_payload, PostToolUsePayload
from tool_input import is_write_tool, get_written_paths
from workspace_utils import to_workspace_relative

SCRIPT_DIR = Path(__file__).resolve().parent
PATCH_TIMEOUT_SECONDS = 30
DEBUG = HookDebugLogger(SCRIPT_DIR, "post_tool_dashboard_sync")


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------

def _build_patch_cmd(patch_script: Path, changed_file: Optional[str]) -> List[str]:
    """Build the patch_dashboard.py command list.

    changed_file must be a workspace-relative POSIX path or None.
    """
    cmd = [
        sys.executable, str(patch_script),
        "--docs-dir", "docs",
        "--dashboard", "docs/dashboard.md",
    ]
    if changed_file:
        cmd += ["--changed-file", changed_file]
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
# main() phase helpers
# ---------------------------------------------------------------------------

def _parse_input() -> tuple[PostToolUsePayload, HookOutput, str, Path, Path]:
    """Parse stdin payload and resolve workspace context.

    Returns (event, OUT, workspace, workspace_path, patch_script).
    Emits DEBUG.log("input") before returning.
    """
    raw = read_payload()
    event = parse_payload(raw)
    if not isinstance(event, PostToolUsePayload):
        event = PostToolUsePayload.from_dict(raw)
    OUT = HookOutput(event.hook_event_name or "PostToolUse")
    workspace = event.cwd or os.getcwd()
    workspace_path = Path(workspace)
    patch_script = workspace_path / ".github" / "scripts" / "patch_dashboard.py"
    DEBUG.log("input", tool_name=event.tool_name, cwd=workspace)
    return event, OUT, workspace, workspace_path, patch_script



def _should_skip(
    event: PostToolUsePayload,
    workspace_path: Path,
) -> tuple[Optional[str], Optional[str]]:
    """Determine whether this event should be skipped.

    Returns (reason, changed_file).
    reason is None when processing should continue; non-None string when the
    caller should skip (e.g. "non-write tool", "not a docs/ .md file").
    changed_file is the written path extracted from tool_input, or None.
    """
    if not is_write_tool(event.tool_name):
        return "non-write tool", None
    DEBUG.log("tool_input_keys", tool_name=event.tool_name, keys=list(event.tool_input.keys()))
    paths = get_written_paths(event.tool_name, event.tool_input)
    raw_file = paths[0] if paths else None
    if raw_file:
        rel = to_workspace_relative(raw_file, workspace_path)
        if rel is None or not rel.startswith("docs/") or not rel.lower().endswith(".md"):
            return "not a docs/ .md file", raw_file
        changed_file = rel
    else:
        changed_file = None
    return None, changed_file


def _run_dashboard_update(
    patch_script: Path,
    changed_file: Optional[str],
    workspace: str,
    event: PostToolUsePayload,
    OUT: HookOutput,
) -> tuple[subprocess.CompletedProcess, str]:
    """Build the patch command, log it, and run patch_dashboard.py.

    changed_file must be a workspace-relative POSIX path or None.
    Returns (result, cmd_preview). Raises SystemExit on timeout or OS error
    (delegated to _run_patch).
    """
    cmd = _build_patch_cmd(patch_script, changed_file)
    cmd_preview = " ".join(cmd)
    DEBUG.log("start", cwd=workspace, tool_name=event.tool_name,
              changed_file=changed_file, cmd=cmd_preview)
    result = _run_patch(cmd, workspace, cmd_preview, OUT)
    return result, cmd_preview


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    # 1. 入力パース
    event, OUT, workspace, workspace_path, patch_script = _parse_input()
    # 2. Skip判定（対象外は即時終了、I/O不要）
    reason, changed_file = _should_skip(event, workspace_path)
    if reason:
        DEBUG.log("skip", reason=reason)
        return
    # 3. 前提条件のチェック（書き込みツールの場合のみ到達）
    if not patch_script.is_file():
        sys.exit(OUT.warn(f"Dashboard sync hook could not find patch script. cwd={workspace}"))
    # 4. ダッシュボード更新処理
    result, cmd_preview = _run_dashboard_update(
        patch_script, changed_file, workspace, event, OUT
    )
    # 5. result処理
    if result.returncode == 0:
        return  # 何も出力しない（正常終了）
    else:
        sys.exit(OUT.warn(
            "Dashboard sync hook reported an error. "
            f"Check post_tool_dashboard_sync.debug.log. cwd={workspace}; cmd={cmd_preview}"
        ))


if __name__ == "__main__":
    main()
