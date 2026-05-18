#!/usr/bin/env python3
"""tool_input_parser.py — tool_input フィールドからパス・コマンド文字列を抽出するパーサ。

責務:
    tool_name と tool_input の辞書を受け取り、
    書き込みパス・読み取りパス・コマンド文字列をそれぞれ抽出して返す。
    ツール分類の知識はこのモジュールが持ち、呼び出し側は分岐を書かない。

入力:
    tool_name: str — ツール名
    tool_input: Dict[str, Any] — ツール入力辞書

出力:
    get_write_paths() -> List[str]   書き込み対象のファイルパスリスト
    get_read_paths()  -> List[str]   読み取り対象のファイルパスリスト
    get_command_string() -> str      コマンド文字列（COMMAND_TOOLS のみ）

副作用:
    なし（純粋関数群）。

依存モジュール:
    typing（標準ライブラリのみ）
"""

from __future__ import annotations

from typing import Dict, List


# ---------------------------------------------------------------------------
# Write path extraction
# ---------------------------------------------------------------------------

def get_write_paths(tool_name: str, tool_input: Dict) -> List[str]:
    """書き込みツールの tool_input からファイルパスリストを抽出する。

    責務: tool_name に応じた write パスを返す。非 write ツールは空リスト。
    入力: tool_name — 書き込み系ツール名、tool_input — ツール入力辞書。
    出力: 書き込み対象パスの文字列リスト。
    副作用: なし。
    """
    if tool_name == "apply_patch":
        return _parse_apply_patch_paths(tool_input)

    if tool_name == "multi_replace_string_in_file":
        replacements = tool_input.get("replacements") or []
        paths = [r.get("filePath", "") for r in replacements if r.get("filePath")]
        if not paths:
            fp = tool_input.get("filePath", "")
            return [fp] if fp else []
        return paths

    if tool_name == "create_directory":
        dir_path = tool_input.get("dirPath", "")
        return [dir_path] if dir_path else []

    if tool_name in ("replace_string_in_file", "create_file"):
        fp = tool_input.get("filePath", "")
        return [fp] if fp else []

    if tool_name == "edit_notebook_file":
        fp = tool_input.get("filePath", "")
        return [fp] if fp else []

    if tool_name in ("create_new_jupyter_notebook", "create_new_workspace"):
        fp = tool_input.get("filePath", "")
        return [fp] if fp else []

    return []


def _parse_apply_patch_paths(tool_input: Dict) -> List[str]:
    """apply_patch の input フィールドから '*** [Action] File:' 行のパスを抽出する。

    責務: patch テキストの File: 行のみを解析してパスリストを返す。
    入力: tool_input — apply_patch の入力辞書。
    出力: パスの文字列リスト。
    副作用: なし。
    """
    patch_text = tool_input.get("input", "")
    if not isinstance(patch_text, str):
        return []
    paths: List[str] = []
    for line in patch_text.splitlines():
        line = line.strip()
        if not line.startswith("*** ") or " File: " not in line:
            continue
        path_part = line.split(" File: ", 1)[1].strip()
        # rename patch: "old/path -> new/path" — keep source path
        if " -> " in path_part:
            path_part = path_part.split(" -> ", 1)[0].strip()
        if path_part:
            paths.append(path_part)
    return paths


# ---------------------------------------------------------------------------
# Read path extraction
# ---------------------------------------------------------------------------

def get_read_paths(tool_name: str, tool_input: Dict) -> List[str]:
    """読み取りツールの tool_input からファイルパスリストを抽出する。

    責務: tool_name に応じた read パスを返す。非 read ツールは空リスト。
    入力: tool_name — 読み取り系ツール名、tool_input — ツール入力辞書。
    出力: 読み取り対象パスの文字列リスト。
    副作用: なし。
    """
    if tool_name in ("read_file", "view_image"):
        fp = tool_input.get("filePath", "")
        return [fp] if fp else []

    if tool_name in ("read_notebook_cell_output", "copilot_getNotebookSummary"):
        fp = tool_input.get("filePath", "")
        return [fp] if fp else []

    if tool_name == "get_errors":
        file_paths = tool_input.get("filePaths") or []
        return [p for p in file_paths if isinstance(p, str) and p]

    if tool_name == "grep_search":
        # includePattern は探索スコープ指定であり、read 対象パスとしては扱わない。
        return []

    if tool_name == "file_search":
        query = tool_input.get("query", "")
        return [query] if query else []

    if tool_name == "get_changed_files":
        repo_path = tool_input.get("repositoryPath", "")
        return [repo_path] if repo_path else []

    if tool_name == "list_dir":
        directory = tool_input.get("path", "")
        return [directory] if directory else []

    return []


# ---------------------------------------------------------------------------
# Command string extraction
# ---------------------------------------------------------------------------

def get_command_string(tool_input: Dict) -> str:
    """コマンド実行ツールの tool_input からコマンド文字列を抽出する。

    責務: tool_input の command キーまたは task.command + task.args を返す。
    入力: tool_input — コマンド系ツールの入力辞書。
    出力: コマンド文字列。取得できない場合は空文字列。
    副作用: なし。
    """
    if "command" in tool_input and isinstance(tool_input.get("command"), str):
        return tool_input["command"]

    if isinstance(tool_input.get("task"), dict):
        task = tool_input["task"]
        cmd = task.get("command", "")
        if not isinstance(cmd, str) or not cmd:
            return ""
        args = task.get("args") or []
        if isinstance(args, list):
            arg_str = " ".join(str(a) for a in args)
            return f"{cmd} {arg_str}".strip()
        return cmd

    return ""
