#!/usr/bin/env python3
"""access_control: PreToolUse hook — ファイルアクセス制御とコマンド実行制限。

設定ファイル (.github/hooks/config/access-control.json) に定義されたルールに基づき、
ツール呼び出しを deny（ブロック）または confirm（確認要求）する。

Debug enable/disable
--------------------
ON  : create  .github/hooks/scripts/access_control.debug
OFF : delete  .github/hooks/scripts/access_control.debug

Log file : .github/hooks/scripts/access_control.debug.log
"""

from __future__ import annotations

import sys
from pathlib import Path

from debug_logging import HookDebugLogger
from hook_payload import read_payload, parse_payload, PreToolUsePayload
from ac_config_loader import load_config
from ac_rule_engine import MatchContext, RuleMatch, evaluate

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR.parent / "config" / "access-control.json"

DEBUG = HookDebugLogger(SCRIPT_DIR, "access_control")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_reason(rule_match: RuleMatch) -> str:
    """ユーザー向けのブロック/確認理由メッセージを構築する。"""
    rule = rule_match.rule
    parts = []
    if rule.description:
        parts.append(rule.description)
    if rule_match.matched_values:
        parts.append(f"対象: {', '.join(rule_match.matched_values)}")
    parts.append(f"ルールID: {rule.rule_id}")
    return " | ".join(parts)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    try:
        raw = read_payload()
        event = parse_payload(raw)
        DEBUG.log("input", hook_event=event.hook_event_name)

        if not isinstance(event, PreToolUsePayload):
            return

        try:
            config = load_config(CONFIG_PATH)
        except FileNotFoundError:
            DEBUG.log("skip", reason="config not found", path=str(CONFIG_PATH))
            sys.exit(event.warn(
                f"⚠ アクセス制御設定ファイルが見つかりません。設定ファイルを作成するか、Hookを無効にしてください:\n"
                f"  期待パス: {CONFIG_PATH}"
            ))
        except Exception as exc:
            DEBUG.log("error", stage="load_config", exc=str(exc))
            sys.exit(event.warn(
                f"⚠ アクセス制御設定ファイルの読み込みに失敗しました。設定ファイルを修正してください:\n"
                f"  ファイル: {CONFIG_PATH}\n"
                f"  エラー: {exc}"
            ))

        context = MatchContext(
            tool_name=event.tool_name,
            tool_input=event.tool_input,
            cwd=event.cwd,
        )

        config_warning = (
            "⚠ アクセス制御設定に不正なルールが含まれています。設定ファイルを修正してください:\n"
            + "\n".join(f"  - {msg}" for msg in config.skipped_rules)
            if config.skipped_rules else ""
        )

        result = evaluate(config, context)
        DEBUG.log(
            "evaluate",
            tool=event.tool_name,
            match_id=result.rule.rule_id if result else None,
            action=result.rule.action if result else "allow",
            skipped=len(config.skipped_rules),
        )

        if result is None:
            if config_warning:
                sys.exit(event.warn(config_warning))
            return

        reason = _build_reason(result)
        if config_warning:
            reason = f"{reason}\n\n{config_warning}"

        if result.rule.action == "deny":
            sys.exit(event.deny(reason))

        if result.rule.action == "confirm":
            sys.exit(event.ask(reason))

    except SystemExit:
        raise
    except Exception as exc:
        DEBUG.log("error", exc=str(exc))


if __name__ == "__main__":
    main()
