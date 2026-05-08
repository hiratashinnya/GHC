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
class AccessControlConfig:
    """アクセス制御設定全体。

    拡張ガイド:
        新しい操作タイプを追加する場合は、このクラスにフィールドを追加し、
        load_config() と ac_rule_engine.py の _get_candidate_rules() を更新する。
    """
    description: str = ""
    version: str = "1.0"
    write_rules: List[Rule] = field(default_factory=list)
    read_rules: List[Rule] = field(default_factory=list)
    command_rules: List[Rule] = field(default_factory=list)


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


def _parse_rule_list(raw_list: object) -> List[Rule]:
    if not isinstance(raw_list, list):
        return []
    return [_parse_rule(item) for item in raw_list if isinstance(item, dict)]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_config(config_path: Path) -> AccessControlConfig:
    """アクセス制御設定を JSON ファイルから読み込む。

    Raises:
        FileNotFoundError: ファイルが存在しない場合。
        ValueError: action に無効な値が含まれる場合。
        json.JSONDecodeError: JSON の構文エラー。
    """
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    return AccessControlConfig(
        description=raw.get("description", ""),
        version=raw.get("version", "1.0"),
        write_rules=_parse_rule_list(raw.get("write_rules")),
        read_rules=_parse_rule_list(raw.get("read_rules")),
        command_rules=_parse_rule_list(raw.get("command_rules")),
    )
