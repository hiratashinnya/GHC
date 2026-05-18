#!/usr/bin/env python3
"""ac_rule_engine.py — Rule evaluation engine for the access control hook.

責務:
    ツール呼び出しコンテキストとアクセス制御設定を照合し、
    適用すべきアクション（deny / confirm / allow）を決定する。

入力 / 出力:
    evaluate(config: AccessControlConfig, context: MatchContext) -> Optional[RuleMatch]
    - マッチするルールがなければ None (= allow)
    - 複数マッチ時は deny > confirm の優先度で最上位のルールを返す
    - action="disabled" のルールは評価対象外

副作用:
    なし（純粋関数群）。

依存モジュール:
    fnmatch, dataclasses, pathlib, typing (標準ライブラリ)
    ac_config_loader (本プロジェクト)

拡張ガイド:
    新しい操作タイプ（例: "network"）を追加する場合:
        1. NETWORK_TOOLS frozenset を追加する
        2. _determine_operation_type() に elif を追加する
        3. _get_candidate_rules() に elif を追加する
        4. _matches_rule() に対応する条件分岐を追加する
        5. ac_config_loader.py / access-control.json に network_rules を追加する

    MatchContext に新フィールド（agent_id 等）を追加する場合:
        1. MatchContext dataclass にフィールドを追加する
        2. _matches_rule() 内で WhenClause の対応フィールドをチェックする
        （access_control.py 側でコンテキスト生成時にフィールドを渡す）
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Dict, List, Optional

from ac_config_loader import AccessControlConfig, Rule
import re
from debug_logging import HookDebugLogger
from tool_input_parser import get_write_paths, get_read_paths, get_command_string

# ---------------------------------------------------------------------------
# Tool classification
# ---------------------------------------------------------------------------

WRITE_TOOLS: frozenset = frozenset({
    "apply_patch",
    "replace_string_in_file",
    "create_file",
    "multi_replace_string_in_file",
    "create_directory",
    "edit_notebook_file",
    "create_new_jupyter_notebook",
    "create_new_workspace",
})

READ_TOOLS: frozenset = frozenset({
    "read_file",
    "list_dir",
    "view_image",
    "file_search",
    "grep_search",
    "get_errors",
    "read_notebook_cell_output",
    "copilot_getNotebookSummary",
    "get_changed_files",
})

COMMAND_TOOLS: frozenset = frozenset({
    "run_in_terminal",
    "send_to_terminal",
    "create_and_run_task",
})

# deny > confirm（priority リストの先頭が最優先）
_ACTION_PRIORITY: List[str] = ["deny", "confirm"]

# ---------------------------------------------------------------------------
# Public dataclasses
# ---------------------------------------------------------------------------


@dataclass
class MatchContext:
    """ツール呼び出し時のコンテキスト。ルールマッチングに使用する。

    拡張ガイド:
        新しいマッチ条件（agent_id, session_scope 等）はここにフィールドを追加し、
        _matches_rule() と WhenClause（ac_config_loader.py）にも対応フィールドを追加する。
    """
    tool_name: str = ""
    tool_input: Dict = field(default_factory=dict)
    cwd: str = ""


@dataclass
class RuleMatch:
    """マッチしたルールと、マッチした値（パスまたはコマンドパターン）。"""
    rule: Rule
    matched_values: List[str] = field(default_factory=list)

    def to_reason(self) -> str:
        """ユーザー向けのブロック/確認理由メッセージを返す。"""
        parts = []
        if self.rule.description:
            parts.append(self.rule.description)
        if self.matched_values:
            parts.append(f"対象: {', '.join(self.matched_values)}")
        parts.append(f"ルールID: {self.rule.rule_id}")
        return " | ".join(parts)


# ---------------------------------------------------------------------------
# Path / command extraction helpers
# ---------------------------------------------------------------------------

def _get_paths_from_tool_input(tool_name: str, tool_input: Dict) -> List[str]:
    """tool_input からファイルパスのリストを抽出する（tool_input_parser に委譲）。"""
    if tool_name in WRITE_TOOLS:
        return get_write_paths(tool_name, tool_input)
    return get_read_paths(tool_name, tool_input)


def _get_command_from_tool_input(tool_input: Dict) -> str:
    """tool_input からコマンド文字列を取得する（tool_input_parser に委譲）。"""
    return get_command_string(tool_input)


def _to_posix_relative(path_str: str, cwd: str) -> str:
    """パスを forward-slash・ワークスペース相対に正規化する。

    絶対パスかつ cwd が判明している場合は cwd で相対化を試みる。
    相対化できない場合はそのまま forward-slash に変換して返す。

    # Note: workspace_utils.to_workspace_relative への置換は不採用。
    # 理由: workspace 外の絶対パス（例: D:/other/... 形式）を評価対象として残すために
    # None を返す同関数へ置き換えてしまうと、ブロックルールが到達しなくなる。
    """
    if not path_str:
        return ""
    path = Path(path_str)
    if path.is_absolute() and cwd:
        try:
            path = path.relative_to(cwd)
        except ValueError:
            pass
    return PurePosixPath(path).as_posix()


# ---------------------------------------------------------------------------
# Matching helpers
# ---------------------------------------------------------------------------

def _match_single_path(normalized: str, pattern: str) -> bool:
    """1パスが1パターンにマッチするか判定する。

    ``**/`` プレフィックスを持つパターンはルート直下のファイルにも適用する。
    例: ``**/.env`` は ``.env``（ルート直下）と ``subdir/.env`` 両方にマッチする。
    """
    if fnmatch.fnmatch(normalized, pattern):
        return True
    # "**/.env" のようなパターンはルート直下（"/" なし）にも適用する
    if pattern.startswith("**/"):
        if fnmatch.fnmatch(normalized, pattern[3:]):
            return True
    return False


def _match_path_patterns(patterns: List[str], paths: List[str], cwd: str) -> List[str]:
    """glob パターンにマッチしたパスのリストを返す。"""
    matched = []
    for path_str in paths:
        normalized = _to_posix_relative(path_str, cwd)
        for pattern in patterns:
            if _match_single_path(normalized, pattern):
                matched.append(path_str)
                break
    return matched


def _match_command_patterns(patterns: List[str], command: str, debug: Optional[HookDebugLogger] = None) -> List[str]:
    """Command patterns are matched as regexes with IGNORECASE flag."""
    matched = []
    for pattern in patterns:
        try:
            if re.search(pattern, command, re.IGNORECASE):
                matched.append(pattern)
        except re.error as exc:
            if debug:
                debug.log("regex_error", log_type="regex_error", pattern=pattern, error=str(exc))
    return matched


def _matches_rule(
    rule: Rule,
    context: MatchContext,
    operation_type: str,
    debug: Optional[HookDebugLogger] = None,
) -> Optional[RuleMatch]:
    """ルールがコンテキストにマッチするか判定する。マッチすれば RuleMatch を返す。

    拡張ガイド:
        新しい when フィールド（agent_id 等）は、ここに対応する条件チェックを追加する。
        各チェックは独立したブロックとして実装し、AND 条件で評価することを推奨する。
    """
    when = rule.when

    if operation_type in ("write", "read"):
        paths = _get_paths_from_tool_input(context.tool_name, context.tool_input)
        if when.path_patterns:
            matched = _match_path_patterns(when.path_patterns, paths, context.cwd)
            if matched:
                return RuleMatch(rule=rule, matched_values=matched)
            return None
        # path_patterns 未指定 → 全パスにマッチ
        return RuleMatch(rule=rule, matched_values=paths)

    if operation_type == "command":
        command = _get_command_from_tool_input(context.tool_input)
        if when.command_patterns:
            matched_patterns = _match_command_patterns(when.command_patterns, command, debug=debug)
            if matched_patterns:
                return RuleMatch(rule=rule, matched_values=matched_patterns)
            return None
        # command_patterns 未指定 → 全コマンドにマッチ
        return RuleMatch(rule=rule, matched_values=[command] if command else [])

    return None


# ---------------------------------------------------------------------------
# Operation type resolution
# ---------------------------------------------------------------------------

def _determine_operation_type(tool_name: str) -> Optional[str]:
    """ツール名から操作タイプ（"write" / "read" / "command"）を決定する。"""
    if tool_name in WRITE_TOOLS:
        return "write"
    if tool_name in READ_TOOLS:
        return "read"
    if tool_name in COMMAND_TOOLS:
        return "command"
    return None


def _get_candidate_rules(config: AccessControlConfig, operation_type: str) -> List[Rule]:
    """操作タイプに対応するグループが有効な場合そのルールリストを、無効な場合空リストを返す。"""
    group = config.get_group(operation_type)
    return group.rules if group.enabled else []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def evaluate(config: AccessControlConfig, context: MatchContext, debug: Optional[HookDebugLogger] = None) -> Optional[RuleMatch]:
    """適用すべきルールを評価し、優先度が最も高いマッチを返す。

    評価順序:
        1. context.tool_name から操作タイプを決定する
        2. 対応するルールリストを取得する
        3. action="disabled" のルールを除外する
        4. 残りのルールをコンテキストと照合する
        5. マッチしたルールの中から deny > confirm の優先度で1件返す
        6. マッチなし = None (allow)

    Args:
        config: 読み込み済みのアクセス制御設定。
        context: 現在のツール呼び出しコンテキスト。

    Returns:
        最も優先度の高い RuleMatch、またはマッチなしの場合は None。
    """
    operation_type = _determine_operation_type(context.tool_name)
    if operation_type is None:
        return None

    if not config.enabled:
        return None

    candidates = _get_candidate_rules(config, operation_type)

    active_matches: List[RuleMatch] = []
    for rule in candidates:
        if not rule.is_active():
            continue
        match = _matches_rule(rule, context, operation_type, debug=debug)
        if match:
            active_matches.append(match)

    if not active_matches:
        return None

    # 優先度解決: deny > confirm
    for action in _ACTION_PRIORITY:
        for match in active_matches:
            if match.rule.action == action:
                return match

    return None
