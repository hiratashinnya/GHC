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
from typing import List

VALID_ACTIONS: frozenset = frozenset({"deny", "confirm", "disabled"})


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


@dataclass
class Rule:
    """単一のアクセス制御ルール。"""
    rule_id: str = ""
    description: str = ""
    action: str = "disabled"
    when: WhenClause = field(default_factory=WhenClause)

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
    )


def _parse_rule(raw: dict) -> Rule:
    action = raw.get("action", "disabled")
    if action not in VALID_ACTIONS:
        raise ValueError(
            f"ルール {raw.get('id', '(unknown)')!r}: 不正な action {action!r}。"
            f"有効な値: {sorted(VALID_ACTIONS)}"
        )
    return Rule(
        rule_id=raw.get("id", ""),
        description=raw.get("description", ""),
        action=action,
        when=_parse_when(raw.get("when") or {}),
    )


def _parse_rule_list(raw_list: object, errors: List[str]) -> List[Rule]:
    if not isinstance(raw_list, list):
        return []
    rules: List[Rule] = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        try:
            rule = _parse_rule(item)
            # Validate command_patterns as regex
            rule_id = item.get("id", "(unknown)")
            for pattern in rule.when.command_patterns:
                try:
                    re.compile(pattern)
                except re.error as exc:
                    errors.append(f"invalid regex in rule {rule_id}: {pattern} - {exc}")
            rules.append(rule)
        except ValueError as exc:
            # 不正なルールはスキップし、エラー内容を errors に収集してユーザーへの通知に使う
            errors.append(str(exc))
    return rules


def _parse_rule_group(raw_group: object, errors: List[str]) -> RuleGroup:
    """操作タイプごとのルールグループをパースする。

    配列形式の場合は後方互換として enabled=True のグループとして扱う。
    """
    if isinstance(raw_group, list):
        return RuleGroup(enabled=True, rules=_parse_rule_list(raw_group, errors))
    if isinstance(raw_group, dict):
        raw_enabled = raw_group.get("enabled", True)
        enabled = raw_enabled if isinstance(raw_enabled, bool) else True
        return RuleGroup(
            enabled=enabled,
            rules=_parse_rule_list(raw_group.get("rules") or [], errors),
        )
    return RuleGroup()


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
        skipped_rules=skipped,
    )
