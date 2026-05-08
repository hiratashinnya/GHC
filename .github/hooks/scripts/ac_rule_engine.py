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

# ---------------------------------------------------------------------------
# Tool classification
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

COMMAND_TOOLS: frozenset = frozenset({
    "run_in_terminal",
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


# ---------------------------------------------------------------------------
# Path / command extraction helpers
# ---------------------------------------------------------------------------

def _get_paths_from_tool_input(tool_name: str, tool_input: Dict) -> List[str]:
    """tool_input からファイルパスのリストを抽出する。"""
    if tool_name == "multi_replace_string_in_file":
        replacements = tool_input.get("replacements") or []
        paths = [r.get("filePath", "") for r in replacements if r.get("filePath")]
        if not paths:
            fp = tool_input.get("filePath", "")
            return [fp] if fp else []
        return paths

    if tool_name in ("replace_string_in_file", "create_file"):
        fp = tool_input.get("filePath", "")
        return [fp] if fp else []

    if tool_name in ("read_file", "view_image"):
        fp = tool_input.get("filePath", "")
        return [fp] if fp else []

    if tool_name == "list_dir":
        directory = tool_input.get("path", "")
        return [directory] if directory else []

    return []


def _get_command_from_tool_input(tool_input: Dict) -> str:
    """tool_input からコマンド文字列を取得する。"""
    return tool_input.get("command", "")


def _to_posix_relative(path_str: str, cwd: str) -> str:
    """パスを forward-slash・ワークスペース相対に正規化する。

    絶対パスかつ cwd が判明している場合は cwd で相対化を試みる。
    相対化できない場合はそのまま forward-slash に変換して返す。
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


def _match_command_patterns(patterns: List[str], command: str) -> List[str]:
    """command 文字列に含まれるパターン（部分一致・大小文字無視）のリストを返す。"""
    return [p for p in patterns if p.lower() in command.lower()]


def _matches_rule(
    rule: Rule,
    context: MatchContext,
    operation_type: str,
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
            matched_patterns = _match_command_patterns(when.command_patterns, command)
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
    """操作タイプに対応するルールリストを返す。"""
    if operation_type == "write":
        return config.write_rules
    if operation_type == "read":
        return config.read_rules
    if operation_type == "command":
        return config.command_rules
    return []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def evaluate(config: AccessControlConfig, context: MatchContext) -> Optional[RuleMatch]:
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

    candidates = _get_candidate_rules(config, operation_type)

    active_matches: List[RuleMatch] = []
    for rule in candidates:
        if not rule.is_active():
            continue
        match = _matches_rule(rule, context, operation_type)
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
