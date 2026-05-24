#!/usr/bin/env python3
"""access_control: PreToolUse hook — ファイルアクセス制御とコマンド実行制限。

設定ファイル (.github/hooks/config/access-control.json) に定義されたルールに基づき、
ツール呼び出しを deny（ブロック）または confirm（確認要求）する。

Debug enable/disable
--------------------
ON  : create  .github/hooks/scripts/entrypoints/access_control.debug
OFF : delete  .github/hooks/scripts/entrypoints/access_control.debug

Log file : .github/hooks/scripts/entrypoints/access_control.debug.log
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = SCRIPT_DIR.parent
IMPORT_DIRS = (
    SCRIPTS_DIR / "core",
    SCRIPTS_DIR / "access_control",
    SCRIPTS_DIR / "tooling",
    SCRIPTS_DIR / "shared",
)
for import_dir in IMPORT_DIRS:
    if str(import_dir) not in sys.path:
        sys.path.insert(0, str(import_dir))

from debug_logging import HookDebugLogger
from hook_payload import get_hook_input, PreToolUsePayload
from ac_config_loader import load_config
from ac_rule_engine import MatchContext, RuleMatch, evaluate

CONFIG_PATH = SCRIPT_DIR.parent.parent / "config" / "access-control.json"

DEBUG = HookDebugLogger(SCRIPT_DIR, "access_control")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_config_or_exit(event: PreToolUsePayload, config_path: Path):
    """設定ファイルを読み込む。失敗時は warn して sys.exit する。"""
    try:
        return load_config(config_path)
    except FileNotFoundError:
        DEBUG.log("skip", reason="config not found", path=str(config_path))
        sys.exit(event.warn(
            f"⚠ アクセス制御設定ファイルが見つかりません。設定ファイルを作成するか、Hookを無効にしてください:\n"
            f"  期待パス: {config_path}"
        ))
    except Exception as exc:
        DEBUG.log("error", stage="load_config", exc=str(exc))
        sys.exit(event.warn(
            f"⚠ アクセス制御設定ファイルの読み込みに失敗しました。設定ファイルを修正してください:\n"
            f"  ファイル: {config_path}\n"
            f"  エラー: {exc}"
        ))


def _build_config_warning(config) -> str:
    """スキップされたルールがある場合に warning 文字列を返す。"""
    if not config.skipped_rules:
        return ""
    return (
        "⚠ アクセス制御設定に不正なルールが含まれています。設定ファイルを修正してください:\n"
        + "\n".join(f"  - {msg}" for msg in config.skipped_rules)
    )


def _dispatch_action(
    event: PreToolUsePayload,
    result: RuleMatch | None,
    config_warning: str,
) -> None:
    """マッチ結果に応じて deny / confirm / warn を発火する。"""
    if result is None:
        if config_warning:
            sys.exit(event.warn(config_warning))
        return

    reason = result.to_reason()
    if config_warning:
        reason = f"{reason}\n\n{config_warning}"

    if result.rule.action == "deny":
        sys.exit(event.deny(reason))
    elif result.rule.action == "confirm":
        sys.exit(event.ask(reason))
    else:
        # allow または unknown: config_warning があれば必ず表示する
        if config_warning:
            sys.exit(event.warn(config_warning))


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    try:
        event = get_hook_input(debug=DEBUG)
        DEBUG.log(
            "input",
            hook_event=event.hook_event_name,
            tool_name=getattr(event, "tool_name", ""),
            keys=list(getattr(event, "tool_input", {}).keys()),
        )

        if not isinstance(event, PreToolUsePayload):
            return

        config = _load_config_or_exit(event, CONFIG_PATH)
        config_warning = _build_config_warning(config)

        context = MatchContext(
            tool_name=event.tool_name,
            tool_input=event.tool_input,
            cwd=event.cwd,
        )

        result = evaluate(config, context, debug=DEBUG)
        DEBUG.log(
            "evaluate",
            tool=event.tool_name,
            match_id=result.rule.rule_id if result else None,
            action=result.rule.action if result else "allow",
            skipped=len(config.skipped_rules),
        )

        _dispatch_action(event, result, config_warning)

    except SystemExit:
        raise
    except Exception as exc:
        DEBUG.log("error", exc=str(exc))


if __name__ == "__main__":
    main()
