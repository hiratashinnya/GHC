#!/usr/bin/env python3
"""ac_config_loader.py — Access control config loader for hook scripts.

責務:
    .github/hooks/config/access-control.json を読み込み、型付き dataclass に変換する。
    設定ファイルの構造検証（不正なaction値の検出）も行う。

入力 / 出力:
    load_config(path: Path) -> AccessControlConfig

副作用:
    なし（ファイル読み取りのみ）。

依存モジュール:
    json, dataclasses, pathlib, typing (標準ライブラリのみ)

拡張ガイド:
    新しい操作タイプ（例: network_rules）を追加する場合:
    1. AccessControlConfig に新フィールドを追加する
    2. load_config() の raw.get() 行を1行追加する
    それ以外の変更は不要。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional, Tuple, TypeVar

VALID_ACTIONS: frozenset = frozenset({"deny", "confirm", "disabled"})
VALID_ARBITRATIONS: frozenset = frozenset({"blacklist", "confirm", "whitelist"})


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class WhenClause:
    """ルールが発動する条件。

    拡張ガイド:
        agent-scope や session_scope 等の新条件は、このクラスに新フィールドを追加し、
        ac_rule_engine.py の _matches_rule() に対応するマッチャーを追加するだけでよい。
    """
    path_patterns: List[str] = field(default_factory=list)
    command_patterns: List[str] = field(default_factory=list)
    scope_patterns: List[str] = field(default_factory=list)


@dataclass
class RuleBase:
    """ルール共通データ。"""

    rule_id: str = ""
    description: str = ""
    when: WhenClause = field(default_factory=WhenClause)


@dataclass
class Rule(RuleBase):
    """単一のアクセス制御ルール。"""

    action: str = "disabled"

    def is_active(self) -> bool:
        """action が "disabled" でない場合に True を返す。"""
        return self.action != "disabled"


@dataclass
class RuleGroup:
    """操作タイプごとのルールグループ。enabled でグループ単位の有効/無効を切り替えられる。

    拡張ガイド:
        新しい操作タイプを追加する際にこのクラスは変更不要。
        AccessControlConfig に新フィールドを追加するだけでよい。
    """
    enabled: bool = True
    rules: List[Rule] = field(default_factory=list)


@dataclass
class WhitelistRule(RuleBase):
    """ホワイトリストの単一設定項目。"""

    enabled: bool = True
    arbitration: str = "blacklist"

    def is_active(self) -> bool:
        """Return whether this whitelist rule is active."""
        return self.enabled


@dataclass
class WhitelistRuleGroup:
    """操作タイプごとのホワイトリスト設定。"""

    enabled: bool = True
    arbitration: str = "blacklist"
    rules: List[WhitelistRule] = field(default_factory=list)


@dataclass
class WhitelistConfig:
    """ホワイトリスト機能全体の設定。"""

    enabled: bool = False
    arbitration: str = "blacklist"
    write_rules: WhitelistRuleGroup = field(default_factory=WhitelistRuleGroup)
    read_rules: WhitelistRuleGroup = field(default_factory=WhitelistRuleGroup)
    command_rules: WhitelistRuleGroup = field(default_factory=WhitelistRuleGroup)

    def get_group(self, operation_type: str) -> WhitelistRuleGroup:
        mapping = {
            "write": self.write_rules,
            "read": self.read_rules,
            "command": self.command_rules,
        }
        return mapping.get(operation_type, WhitelistRuleGroup())


@dataclass
class AccessControlConfig:
    """アクセス制御設定全体。

    enabled でフック全体を一括で有効/無効にできる。
    各 rules グループの enabled で操作タイプ単位に切り替えられる。
    個別ルールは action="disabled" で切り替えられる。

    拡張ガイド:
        新しい操作タイプを追加する場合は、このクラスにフィールドを追加し、
        load_config() と ac_rule_engine.py の _get_candidate_rules() を更新する。
    """
    enabled: bool = True
    description: str = ""
    version: str = "1.0"
    write_rules: RuleGroup = field(default_factory=RuleGroup)
    read_rules: RuleGroup = field(default_factory=RuleGroup)
    command_rules: RuleGroup = field(default_factory=RuleGroup)
    whitelist: WhitelistConfig = field(default_factory=WhitelistConfig)
    skipped_rules: List[str] = field(default_factory=list)

    def get_group(self, operation_type: str) -> "RuleGroup":
        """operation_type に対応する RuleGroup を返す。未知の操作タイプは空 RuleGroup を返す。"""
        mapping = {
            "write": self.write_rules,
            "read": self.read_rules,
            "command": self.command_rules,
        }
        return mapping.get(operation_type, RuleGroup())


# ---------------------------------------------------------------------------
# Internal parsers
# ---------------------------------------------------------------------------

def _parse_when(raw_when: dict) -> WhenClause:
    return WhenClause(
        path_patterns=list(raw_when.get("path_patterns") or []),
        command_patterns=list(raw_when.get("command_patterns") or []),
        scope_patterns=list(raw_when.get("scope_patterns") or []),
    )


def _to_bool(raw: object, default: bool) -> bool:
    return raw if isinstance(raw, bool) else default


def _parse_arbitration(raw: object, default: str, errors: List[str], context: str) -> str:
    value = raw if isinstance(raw, str) else default
    if value not in VALID_ARBITRATIONS:
        errors.append(
            f"{context}: 不正な arbitration {value!r}。有効な値: {sorted(VALID_ARBITRATIONS)}"
        )
        return default
    return value


def _parse_rule_base(raw: dict) -> RuleBase:
    return RuleBase(
        rule_id=raw.get("id", ""),
        description=raw.get("description", ""),
        when=_parse_when(raw.get("when") or {}),
    )


def _parse_group_payload(raw_group: object) -> Optional[Tuple[bool, object]]:
    if isinstance(raw_group, list):
        return True, raw_group
    if isinstance(raw_group, dict):
        return _to_bool(raw_group.get("enabled", True), True), (raw_group.get("rules") or [])
    return None


def _parse_rule(raw: dict) -> Rule:
    action = raw.get("action", "disabled")
    if action not in VALID_ACTIONS:
        raise ValueError(
            f"ルール {raw.get('id', '(unknown)')!r}: 不正な action {action!r}。"
            f"有効な値: {sorted(VALID_ACTIONS)}"
        )
    base = _parse_rule_base(raw)
    return Rule(
        rule_id=base.rule_id,
        description=base.description,
        action=action,
        when=base.when,
    )


RuleT = TypeVar("RuleT")


def _parse_rule_items(
    raw_list: object,
    parse_item: Callable[[dict], RuleT],
    errors: List[str],
    after_parse: Optional[Callable[[dict, RuleT], None]] = None,
) -> List[RuleT]:
    if not isinstance(raw_list, list):
        return []

    rules: List[RuleT] = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        try:
            parsed = parse_item(item)
            if after_parse:
                after_parse(item, parsed)
            rules.append(parsed)
        except ValueError as exc:
            errors.append(str(exc))
    return rules


def _parse_rule_list(raw_list: object, errors: List[str]) -> List[Rule]:
    def _validate_command_patterns(item: dict, rule: Rule) -> None:
        # Validate command_patterns as regex
        rule_id = item.get("id", "(unknown)")
        for pattern in rule.when.command_patterns:
            try:
                re.compile(pattern)
            except re.error as exc:
                errors.append(f"invalid regex in rule {rule_id}: {pattern} - {exc}")

    return _parse_rule_items(raw_list, _parse_rule, errors, after_parse=_validate_command_patterns)


def _parse_rule_group(raw_group: object, errors: List[str]) -> RuleGroup:
    """操作タイプごとのルールグループをパースする。

    配列形式の場合は後方互換として enabled=True のグループとして扱う。
    """
    payload = _parse_group_payload(raw_group)
    if payload is not None:
        enabled, rules_raw = payload
        return RuleGroup(enabled=enabled, rules=_parse_rule_list(rules_raw, errors))
    return RuleGroup()


def _parse_whitelist_rule(raw: dict, errors: List[str], default_arbitration: str) -> WhitelistRule:
    base = _parse_rule_base(raw)
    arbitration = _parse_arbitration(
        raw.get("arbitration"),
        default_arbitration,
        errors,
        f"whitelist rule {base.rule_id or '(unknown)'}",
    )
    return WhitelistRule(
        rule_id=base.rule_id,
        description=base.description,
        enabled=_to_bool(raw.get("enabled", True), True),
        arbitration=arbitration,
        when=base.when,
    )


def _parse_whitelist_rule_list(
    raw_list: object, errors: List[str], default_arbitration: str
) -> List[WhitelistRule]:
    return _parse_rule_items(
        raw_list,
        lambda item: _parse_whitelist_rule(item, errors, default_arbitration),
        errors,
    )


def _parse_whitelist_group(
    raw_group: object, errors: List[str], default_arbitration: str
) -> WhitelistRuleGroup:
    payload = _parse_group_payload(raw_group)
    if payload is not None:
        enabled, rules_raw = payload
        if isinstance(raw_group, dict):
            group_arbitration = _parse_arbitration(
                raw_group.get("arbitration"),
                default_arbitration,
                errors,
                "whitelist group",
            )
        else:
            group_arbitration = default_arbitration

        return WhitelistRuleGroup(
            enabled=enabled,
            arbitration=group_arbitration,
            rules=_parse_whitelist_rule_list(rules_raw, errors, group_arbitration),
        )
    return WhitelistRuleGroup(arbitration=default_arbitration)


def _parse_whitelist(raw_whitelist: object, errors: List[str]) -> WhitelistConfig:
    if not isinstance(raw_whitelist, dict):
        return WhitelistConfig()

    global_arbitration = _parse_arbitration(
        raw_whitelist.get("arbitration"),
        "blacklist",
        errors,
        "whitelist",
    )
    return WhitelistConfig(
        enabled=_to_bool(raw_whitelist.get("enabled", False), False),
        arbitration=global_arbitration,
        write_rules=_parse_whitelist_group(raw_whitelist.get("write_rules"), errors, global_arbitration),
        read_rules=_parse_whitelist_group(raw_whitelist.get("read_rules"), errors, global_arbitration),
        command_rules=_parse_whitelist_group(raw_whitelist.get("command_rules"), errors, global_arbitration),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_config(config_path: Path) -> AccessControlConfig:
    """アクセス制御設定を JSON ファイルから読み込む。

    Raises:
        FileNotFoundError: ファイルが存在しない場合。
        json.JSONDecodeError: JSON の構文エラー。

    Note:
        action に無効な値を持つルールは ValueError を送出せず当該ルールのみスキップする。
    """
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    skipped: List[str] = []
    raw_enabled = raw.get("enabled", True)
    enabled = raw_enabled if isinstance(raw_enabled, bool) else True
    return AccessControlConfig(
        enabled=enabled,
        description=raw.get("description", ""),
        version=raw.get("version", "1.0"),
        write_rules=_parse_rule_group(raw.get("write_rules"), skipped),
        read_rules=_parse_rule_group(raw.get("read_rules"), skipped),
        command_rules=_parse_rule_group(raw.get("command_rules"), skipped),
        whitelist=_parse_whitelist(raw.get("whitelist"), skipped),
        skipped_rules=skipped,
    )
