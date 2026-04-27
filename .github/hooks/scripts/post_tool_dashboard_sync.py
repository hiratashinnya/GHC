#!/usr/bin/env python3
"""PostToolUse hook: update docs/dashboard.md after tool execution.

This script runs D-3 (patch_dashboard.py), which internally rebuilds the
status matrix and bottleneck sections from docs frontmatter.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional

from debug_logging import HookDebugLogger

SCRIPT_DIR = Path(__file__).resolve().parent
PATCH_TIMEOUT_SECONDS = 30
DEBUG = HookDebugLogger(SCRIPT_DIR, "post_tool_dashboard_sync")


def out_json(data: Dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _read_hook_input() -> Optional[Dict]:
    if sys.stdin.isatty():
        return None
    try:
        raw = sys.stdin.read().strip()
    except OSError:
        return None
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def main() -> None:
    payload = _read_hook_input() or {}
    workspace = payload.get("cwd") or os.getcwd()
    workspace_path = Path(workspace)
    patch_script = workspace_path / ".github" / "scripts" / "patch_dashboard.py"

    # AI が書き込んだファイルパスを tool_input から取得する。
    # Copilot のファイル書き込みツールは "path" キーを使う。
    tool_input = payload.get("tool_input") or {}
    changed_file: Optional[str] = tool_input.get("path") or tool_input.get("file_path")

    # docs/ 配下の .md でなければ dashboard 更新は不要なのでスキップ
    docs_dir = workspace_path / "docs"
    if changed_file:
        changed_path = Path(changed_file) if os.path.isabs(changed_file) else workspace_path / changed_file
        try:
            changed_path.resolve().relative_to(docs_dir.resolve())
            is_docs_md = changed_path.suffix.lower() == ".md"
        except ValueError:
            is_docs_md = False
        if not is_docs_md:
            DEBUG.log("skip", reason="not a docs/ .md file", changed_file=changed_file)
            out_json({"continue": True})
            return

    cmd = [
        sys.executable,
        str(patch_script),
        "--docs-dir",
        "docs",
        "--dashboard",
        "docs/dashboard.md",
    ]
    if changed_file:
        # 相対パスに正規化（patch_dashboard.py 側も同様に処理）
        try:
            rel = str(Path(changed_file).resolve().relative_to(workspace_path.resolve()))
        except ValueError:
            rel = changed_file
        cmd += ["--changed-file", rel]

    cmd_preview = " ".join(cmd)

    DEBUG.log("start", cwd=workspace, tool_name=payload.get("tool_name"), changed_file=changed_file, cmd=cmd_preview)

    if not patch_script.is_file():
        out_json(
            {
                "continue": True,
                "systemMessage": (
                    "Dashboard sync hook could not find patch script. "
                    f"cwd={workspace}; cmd={cmd_preview}"
                ),
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": f"missing script: {patch_script}",
                },
            }
        )
        return

    try:
        result = subprocess.run(
            cmd,
            cwd=workspace,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=PATCH_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        DEBUG.log("timeout", cwd=workspace, cmd=cmd_preview, timeout_seconds=PATCH_TIMEOUT_SECONDS)
        out_json(
            {
                "continue": True,
                "systemMessage": (
                    "Dashboard sync hook timed out. "
                    f"cwd={workspace}; cmd={cmd_preview}; timeout={PATCH_TIMEOUT_SECONDS}s"
                ),
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": (str(exc) or "patch_dashboard.py timed out")[-1200:],
                },
            }
        )
        return
    except OSError as exc:
        DEBUG.log("launch_error", cwd=workspace, cmd=cmd_preview, error=str(exc))
        out_json(
            {
                "continue": True,
                "systemMessage": (
                    "dashboard update hook failed to launch: "
                    f"{exc}; cwd={workspace}; cmd={cmd_preview}"
                ),
            }
        )
        return

    DEBUG.log(
        "done",
        returncode=result.returncode,
        stdout=result.stdout[-1000:],
        stderr=result.stderr[-1000:],
    )

    if result.returncode == 0:
        out_json(
            {
                "continue": True,
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": "Dashboard synchronized from latest document frontmatter.",
                },
            }
        )
    else:
        out_json(
            {
                "continue": True,
                "systemMessage": (
                    "Dashboard sync hook reported an error. "
                    "Check .github/hooks/scripts/post_tool_dashboard_sync.debug.log. "
                    f"cwd={workspace}; cmd={cmd_preview}"
                ),
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": (result.stderr or result.stdout or "patch_dashboard.py returned non-zero")[-1200:],
                },
            }
        )
    return

if __name__ == "__main__":
    main()
