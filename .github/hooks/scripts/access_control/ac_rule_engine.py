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
from dataclasses import dataclass, field, replace
from enum import Enum, auto
from pathlib import Path, PurePosixPath
from typing import Dict, List, Optional

from ac_config_loader import AccessControlConfig, Rule, WhitelistRule, VALID_ARBITRATIONS
import re
from debug_logging import HookDebugLogger
from tool_input_parser import (
    classify_read_input,
    get_write_paths,
    get_read_paths,
    get_command_string,
)

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
_ARBITRATION_PRIORITY: List[str] = ["blacklist", "confirm", "whitelist"]


class OperationType(Enum):
    """Operation kind derived from a tool name."""

    WRITE = "write"
    READ = "read"
    COMMAND = "command"


class OverlapKind(Enum):
    """Classification for overlap between a requested scope and a protected scope."""

    DEFINITE_INCLUSION = auto()
    DEFINITE_DISJOINT = auto()
    UNCERTAIN_OVERLAP = auto()

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


def _literal_prefix(pattern: str) -> str:
    """Return the literal path prefix before any wildcard segment."""
    parts = [part for part in pattern.split("/") if part]
    prefix_parts: List[str] = []
    for part in parts:
        if any(token in part for token in ("*", "?", "[")):
            break
        prefix_parts.append(part)
    return "/".join(prefix_parts)


def _has_extra_constraints(pattern: str, prefix: str) -> bool:
    """Return True when pattern constrains matches beyond a plain recursive subtree."""
    if not prefix:
        return pattern not in ("**", "**/*", "*")
    recursive_forms = {f"{prefix}/**", f"{prefix}/**/*", prefix}
    return pattern not in recursive_forms


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


def _classify_overlap(request: str, rule: str) -> OverlapKind:
    """Classify overlap relationship between glob patterns 'request' and 'rule'."""
    if not request or not rule:
        return OverlapKind.UNCERTAIN_OVERLAP

    if rule.startswith("**/") and request == rule[3:]:
        return OverlapKind.DEFINITE_INCLUSION

    # request が全カバー → request が rule を確実に包含
    if request in ("**", "**/*", "*"):
        return OverlapKind.DEFINITE_INCLUSION

    request_prefix = _literal_prefix(request)
    rule_prefix = _literal_prefix(rule)

    if request.endswith("/**") or request.endswith("/**/*"):
        if request_prefix and rule_prefix:
            if rule_prefix == request_prefix or rule_prefix.startswith(request_prefix + "/"):
                if _has_extra_constraints(rule, rule_prefix):
                    return OverlapKind.UNCERTAIN_OVERLAP
                return OverlapKind.DEFINITE_INCLUSION

    # 明確に非交差: ルートレベルが異なり、どちらも ** で始まらない
    request_root = request.split("/")[0]
    rule_root = rule.split("/")[0]
    if request_root != "**" and rule_root != "**" and request_root != rule_root:
        return OverlapKind.DEFINITE_DISJOINT
    
    # その他は不確実交差
    return OverlapKind.UNCERTAIN_OVERLAP


def _match_scope_patterns(request: str, patterns: List[str]) -> Optional[OverlapKind]:
    """Return overlap classification for a scope-like request against rule patterns.

    Returns:
        OverlapKind.DEFINITE_INCLUSION if request certainly includes a protected scope,
        OverlapKind.UNCERTAIN_OVERLAP if overlap cannot be ruled out,
        None if all patterns are definitely disjoint.
    """
    if not request or not patterns:
        return None

    has_uncertain = False
    for pattern in patterns:
        overlap = _classify_overlap(request, pattern)
        if overlap == OverlapKind.DEFINITE_INCLUSION:
            return OverlapKind.DEFINITE_INCLUSION
        if overlap == OverlapKind.UNCERTAIN_OVERLAP:
            has_uncertain = True

    if has_uncertain:
        return OverlapKind.UNCERTAIN_OVERLAP
    return None


def _matches_rule(
    rule: Rule,
    context: MatchContext,
    operation_type: OperationType,
    debug: Optional[HookDebugLogger] = None,
) -> Optional[RuleMatch]:
    """ルールがコンテキストにマッチするか判定する。マッチすれば RuleMatch を返す。

    拡張ガイド:
        新しい when フィールド（agent_id 等）は、ここに対応する条件チェックを追加する。
        各チェックは独立したブロックとして実装し、AND 条件で評価することを推奨する。
    """
    when = rule.when

    if operation_type in (OperationType.WRITE, OperationType.READ):
        paths = _get_paths_from_tool_input(context.tool_name, context.tool_input)

        if operation_type == OperationType.WRITE:
            if when.path_patterns:
                matched = _match_path_patterns(when.path_patterns, paths, context.cwd)
                if matched:
                    return RuleMatch(rule=rule, matched_values=matched)
                return None
            return RuleMatch(rule=rule, matched_values=paths)

        concrete_paths: List[str] = []
        scope_values: List[str] = []
        ambiguous_values: List[str] = []
        for path_str in paths:
            input_kind = classify_read_input(context.tool_name, path_str)
            if input_kind == "concrete_paths":
                concrete_paths.append(path_str)
            elif input_kind == "scope_patterns":
                scope_values.append(path_str)
            else:
                ambiguous_values.append(path_str)

        if when.path_patterns:
            matched = _match_path_patterns(when.path_patterns, concrete_paths, context.cwd)
            if matched:
                return RuleMatch(rule=rule, matched_values=matched)

        scope_patterns = when.scope_patterns or when.path_patterns
        if scope_patterns:
            for scope_value in scope_values:
                overlap = _match_scope_patterns(scope_value, scope_patterns)
                if overlap == OverlapKind.DEFINITE_INCLUSION:
                    return RuleMatch(rule=rule, matched_values=[scope_value])
                if overlap == OverlapKind.UNCERTAIN_OVERLAP and rule.action == "confirm":
                    return RuleMatch(rule=rule, matched_values=[scope_value])

        if not paths and context.tool_name in ("grep_search", "file_search"):
            raw_scope_value = ""
            if context.tool_name == "grep_search":
                raw_scope_value = context.tool_input.get("includePattern", "")
            if context.tool_name == "file_search":
                raw_scope_value = context.tool_input.get("query", "")
            if raw_scope_value == "" and rule.action == "confirm":
                return RuleMatch(rule=rule, matched_values=[raw_scope_value])

        if ambiguous_values and rule.action == "confirm":
            return RuleMatch(rule=rule, matched_values=ambiguous_values)

        if not when.path_patterns and not when.scope_patterns:
            return RuleMatch(rule=rule, matched_values=paths)

        return None

    if operation_type == OperationType.COMMAND:
        command = _get_command_from_tool_input(context.tool_input)
        if when.command_patterns:
            matched_patterns = _match_command_patterns(when.command_patterns, command, debug=debug)
            if matched_patterns:
                return RuleMatch(rule=rule, matched_values=matched_patterns)
            return None
        # command_patterns 未指定 → 全コマンドにマッチ
        return RuleMatch(rule=rule, matched_values=[command] if command else [])

    return None


def _matches_whitelist_rule(
    rule: WhitelistRule,
    context: MatchContext,
    operation_type: OperationType,
    debug: Optional[HookDebugLogger] = None,
) -> Optional[RuleMatch]:
    black_rule = Rule(
        rule_id=rule.rule_id,
        description=rule.description,
        action="confirm",
        when=rule.when,
    )
    return _matches_rule(black_rule, context, operation_type, debug=debug)


# ---------------------------------------------------------------------------
# Operation type resolution
# ---------------------------------------------------------------------------

def _determine_operation_type(tool_name: str) -> Optional[OperationType]:
    """ツール名から操作タイプを決定する。"""
    if tool_name in WRITE_TOOLS:
        return OperationType.WRITE
    if tool_name in READ_TOOLS:
        return OperationType.READ
    if tool_name in COMMAND_TOOLS:
        return OperationType.COMMAND
    return None


def _get_candidate_rules(config: AccessControlConfig, operation_type: OperationType) -> List[Rule]:
    """操作タイプに対応するグループが有効な場合そのルールリストを、無効な場合空リストを返す。"""
    group = config.get_group(operation_type.value)
    return group.rules if group.enabled else []


def _select_whitelist_arbitration(
    config: AccessControlConfig, operation_type: OperationType, context: MatchContext, debug: Optional[HookDebugLogger] = None
) -> Optional[str]:
    whitelist = config.whitelist
    if not whitelist.enabled or not whitelist.match_enabled:
        return None

    group = whitelist.get_group(operation_type.value)
    if not group.enabled or not group.match_enabled:
        return None

    matched_arbitrations: List[str] = []
    for rule in group.rules:
        if not rule.is_active():
            continue
        match = _matches_whitelist_rule(rule, context, operation_type, debug=debug)
        if match:
            arbitration = rule.arbitration
            if arbitration in VALID_ARBITRATIONS:
                matched_arbitrations.append(arbitration)

    for arbitration in _ARBITRATION_PRIORITY:
        if arbitration in matched_arbitrations:
            return arbitration

    return None


def _apply_arbitration(black_match: RuleMatch, arbitration: str) -> Optional[RuleMatch]:
    if arbitration == "blacklist":
        return black_match
    if arbitration == "confirm":
        return RuleMatch(
            rule=replace(black_match.rule, action="confirm"),
            matched_values=black_match.matched_values,
        )
    if arbitration == "whitelist":
        return None
    return black_match


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
                arbitration = _select_whitelist_arbitration(
                    config=config,
                    operation_type=operation_type,
                    context=context,
                    debug=debug,
                )
                if arbitration is None:
                    return match
                return _apply_arbitration(match, arbitration)

    return None
