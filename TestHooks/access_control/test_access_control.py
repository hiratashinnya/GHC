#!/usr/bin/env python3
"""Unit tests for ac_config_loader.py and ac_rule_engine.py"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

SCRIPTS_DIR = Path(r"c:\GHC\.github\hooks\scripts")
sys.path.insert(0, str(SCRIPTS_DIR))

from ac_config_loader import (
    WhenClause,
    Rule,
    RuleGroup,
    AccessControlConfig,
    load_config,
    VALID_ACTIONS,
)
from ac_rule_engine import (
    MatchContext,
    RuleMatch,
    evaluate,
    _determine_operation_type,
    _to_posix_relative,
    _match_path_patterns,
    _match_command_patterns,
)
from access_control import (
    _build_config_warning,
    _load_config_or_exit,
    _dispatch_action,
)
from hook_payload import PreToolUsePayload


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_config(tmpdir: Path, data: dict) -> Path:
    path = tmpdir / "access-control.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _make_config(
    write_rules=None,
    read_rules=None,
    command_rules=None,
    enabled=True,
    write_enabled=True,
    read_enabled=True,
    command_enabled=True,
) -> AccessControlConfig:
    return AccessControlConfig(
        enabled=enabled,
        write_rules=RuleGroup(enabled=write_enabled, rules=write_rules or []),
        read_rules=RuleGroup(enabled=read_enabled, rules=read_rules or []),
        command_rules=RuleGroup(enabled=command_enabled, rules=command_rules or []),
    )


def _deny_rule(rule_id: str, path_patterns=None, command_patterns=None) -> Rule:
    return Rule(
        rule_id=rule_id,
        action="deny",
        when=WhenClause(
            path_patterns=path_patterns or [],
            command_patterns=command_patterns or [],
        ),
    )


def _confirm_rule(rule_id: str, path_patterns=None, command_patterns=None) -> Rule:
    return Rule(
        rule_id=rule_id,
        action="confirm",
        when=WhenClause(
            path_patterns=path_patterns or [],
            command_patterns=command_patterns or [],
        ),
    )


def _disabled_rule(rule_id: str, path_patterns=None) -> Rule:
    return Rule(
        rule_id=rule_id,
        action="disabled",
        when=WhenClause(path_patterns=path_patterns or []),
    )


# ---------------------------------------------------------------------------
# ac_config_loader tests
# ---------------------------------------------------------------------------

class TestGetGroup(unittest.TestCase):

    def test_AC070_get_group_write(self):
        """get_group: 'write' → write_rules を返す"""
        rule = _deny_rule("r1", path_patterns=["docs/**"])
        config = _make_config(write_rules=[rule])
        group = config.get_group("write")
        self.assertEqual(group.rules[0].rule_id, "r1")

    def test_AC071_get_group_read(self):
        """get_group: 'read' → read_rules を返す"""
        rule = _deny_rule("r2", path_patterns=["**/.env"])
        config = _make_config(read_rules=[rule])
        group = config.get_group("read")
        self.assertEqual(group.rules[0].rule_id, "r2")

    def test_AC072_get_group_command(self):
        """get_group: 'command' → command_rules を返す"""
        rule = _deny_rule("r3", command_patterns=["rm -rf"])
        config = _make_config(command_rules=[rule])
        group = config.get_group("command")
        self.assertEqual(group.rules[0].rule_id, "r3")

    def test_AC073_get_group_unknown_returns_empty(self):
        """get_group: 未知の操作タイプ → 空 RuleGroup を返す"""
        config = _make_config()
        group = config.get_group("network")
        self.assertIsInstance(group, RuleGroup)
        self.assertEqual(group.rules, [])


class TestLoadConfig(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmppath = Path(self._tmpdir.name)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_AC001_normal_load(self):
        """load_config: 正常読み込み"""
        data = {
            "description": "test",
            "version": "1.0",
            "write_rules": [
                {"id": "r1", "description": "desc1", "action": "deny",
                 "when": {"path_patterns": ["docs/**"]}}
            ],
            "read_rules": [
                {"id": "r2", "action": "confirm",
                 "when": {"path_patterns": ["**/.env"]}}
            ],
            "command_rules": [
                {"id": "r3", "action": "deny",
                 "when": {"command_patterns": ["rm -rf"]}}
            ],
        }
        path = _write_config(self.tmppath, data)
        config = load_config(path)
        self.assertIsInstance(config, AccessControlConfig)
        self.assertEqual(len(config.write_rules.rules), 1)
        self.assertEqual(config.write_rules.rules[0].rule_id, "r1")
        self.assertEqual(config.write_rules.rules[0].action, "deny")
        self.assertEqual(config.write_rules.rules[0].when.path_patterns, ["docs/**"])
        self.assertEqual(len(config.read_rules.rules), 1)
        self.assertEqual(len(config.command_rules.rules), 1)

    def test_AC002_invalid_action_skipped_with_warning(self):
        """load_config: 不正な action のルールはスキップされ、skipped_rules にエラーメッセージが格納される"""
        data = {
            "write_rules": [
                {"id": "bad", "action": "unknown", "when": {}},
                {"id": "good", "action": "deny", "when": {"path_patterns": ["docs/**"]}},
            ]
        }
        path = _write_config(self.tmppath, data)
        config = load_config(path)
        self.assertEqual(len(config.write_rules.rules), 1)
        self.assertEqual(config.write_rules.rules[0].rule_id, "good")
        self.assertEqual(len(config.skipped_rules), 1)
        self.assertIn("bad", config.skipped_rules[0])

    def test_AC003_file_not_found(self):
        """load_config: ファイル不在で FileNotFoundError"""
        with self.assertRaises(FileNotFoundError):
            load_config(Path("/nonexistent/access-control.json"))

    def test_AC003b_invalid_json_raises(self):
        """load_config: JSON 構文エラーで JSONDecodeError"""
        import json
        path = self.tmppath / "broken.json"
        path.write_text("{invalid json", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            load_config(path)

    def test_AC004_empty_rules(self):
        """load_config: ルール空配列"""
        data = {"write_rules": [], "read_rules": [], "command_rules": []}
        path = _write_config(self.tmppath, data)
        config = load_config(path)
        self.assertEqual(config.write_rules.rules, [])
        self.assertEqual(config.read_rules.rules, [])
        self.assertEqual(config.command_rules.rules, [])

    def test_AC001b_backward_compat_array_format(self):
        """load_config: 配列形式 (backward compat) が RuleGroup として読み込まれる"""
        data = {
            "write_rules": [
                {"id": "r1", "action": "deny", "when": {"path_patterns": ["docs/**"]}}
            ]
        }
        path = _write_config(self.tmppath, data)
        config = load_config(path)
        self.assertIsInstance(config.write_rules, RuleGroup)
        self.assertTrue(config.write_rules.enabled)
        self.assertEqual(len(config.write_rules.rules), 1)
        self.assertEqual(config.write_rules.rules[0].rule_id, "r1")

    def test_AC005_disabled_is_not_active(self):
        """Rule.is_active: disabled → False"""
        data = {"write_rules": [{"id": "r1", "action": "disabled", "when": {}}]}
        path = _write_config(self.tmppath, data)
        config = load_config(path)
        self.assertFalse(config.write_rules.rules[0].is_active())

    def test_AC006_parse_when_path_patterns(self):
        """_parse_when: path_patterns を正しく格納する"""
        data = {"write_rules": [{"id": "r1", "action": "deny",
                                  "when": {"path_patterns": ["docs/**", "iter/**"]}}]}
        path = _write_config(self.tmppath, data)
        config = load_config(path)
        self.assertEqual(config.write_rules.rules[0].when.path_patterns, ["docs/**", "iter/**"])

    def test_AC007_parse_when_command_patterns(self):
        """_parse_when: command_patterns を正しく格納する"""
        data = {"command_rules": [{"id": "r1", "action": "deny",
                                    "when": {"command_patterns": ["rm -rf", "rd /s /q"]}}]}
        path = _write_config(self.tmppath, data)
        config = load_config(path)
        self.assertEqual(config.command_rules.rules[0].when.command_patterns, ["rm -rf", "rd /s /q"])


# ---------------------------------------------------------------------------
# ac_rule_engine — write operations
# ---------------------------------------------------------------------------

class TestEvaluateWriteRules(unittest.TestCase):

    def test_AC010_no_rules_allows(self):
        """write: ルールなし → None (allow)"""
        config = _make_config()
        ctx = MatchContext(tool_name="create_file", tool_input={"filePath": "src/main.py"})
        self.assertIsNone(evaluate(config, ctx))

    def test_AC011_path_match_deny(self):
        """write: パスマッチ → deny"""
        config = _make_config(
            write_rules=[_deny_rule("r1", path_patterns=[".github/hooks/scripts/**"])]
        )
        ctx = MatchContext(
            tool_name="create_file",
            tool_input={"filePath": ".github/hooks/scripts/foo.py"},
        )
        result = evaluate(config, ctx)
        self.assertIsNotNone(result)
        self.assertEqual(result.rule.action, "deny")

    def test_AC012_path_match_confirm(self):
        """write: パスマッチ → confirm"""
        config = _make_config(
            write_rules=[_confirm_rule("r1", path_patterns=["docs/**"])]
        )
        ctx = MatchContext(
            tool_name="create_file",
            tool_input={"filePath": "docs/basic-design/01-validation.md"},
        )
        result = evaluate(config, ctx)
        self.assertIsNotNone(result)
        self.assertEqual(result.rule.action, "confirm")

    def test_AC013_path_no_match_allows(self):
        """write: パス不一致 → None"""
        config = _make_config(
            write_rules=[_deny_rule("r1", path_patterns=["docs/**"])]
        )
        ctx = MatchContext(tool_name="create_file", tool_input={"filePath": "src/main.py"})
        self.assertIsNone(evaluate(config, ctx))

    def test_AC014_disabled_allows(self):
        """write: disabled ルール → None"""
        config = _make_config(
            write_rules=[_disabled_rule("r1", path_patterns=["docs/**"])]
        )
        ctx = MatchContext(tool_name="create_file", tool_input={"filePath": "docs/foo.md"})
        self.assertIsNone(evaluate(config, ctx))

    def test_AC015_deny_beats_confirm(self):
        """write: deny > confirm 優先"""
        config = _make_config(
            write_rules=[
                _confirm_rule("r1", path_patterns=["docs/**"]),
                _deny_rule("r2", path_patterns=["docs/**"]),
            ]
        )
        ctx = MatchContext(tool_name="create_file", tool_input={"filePath": "docs/foo.md"})
        result = evaluate(config, ctx)
        self.assertIsNotNone(result)
        self.assertEqual(result.rule.action, "deny")

    def test_AC016_replace_string_in_file(self):
        """write: replace_string_in_file パスマッチ"""
        config = _make_config(
            write_rules=[_deny_rule("r1", path_patterns=[".github/hooks/config/**"])]
        )
        ctx = MatchContext(
            tool_name="replace_string_in_file",
            tool_input={"filePath": ".github/hooks/config/foo.json"},
        )
        result = evaluate(config, ctx)
        self.assertIsNotNone(result)
        self.assertEqual(result.rule.action, "deny")

    def test_AC017_multi_replace_multiple_paths(self):
        """write: multi_replace_string_in_file — 複数パスのうち1件がマッチ"""
        config = _make_config(
            write_rules=[_deny_rule("r1", path_patterns=["docs/**"])]
        )
        ctx = MatchContext(
            tool_name="multi_replace_string_in_file",
            tool_input={
                "replacements": [
                    {"filePath": "docs/a.md", "oldString": "x", "newString": "y"},
                    {"filePath": "src/b.py", "oldString": "x", "newString": "y"},
                ]
            },
        )
        result = evaluate(config, ctx)
        self.assertIsNotNone(result)
        self.assertIn("docs/a.md", result.matched_values)


# ---------------------------------------------------------------------------
# ac_rule_engine — read operations
# ---------------------------------------------------------------------------

class TestEvaluateReadRules(unittest.TestCase):

    def test_AC020_no_rules_allows(self):
        """read: ルールなし → None"""
        config = _make_config()
        ctx = MatchContext(tool_name="read_file", tool_input={"filePath": "README.md"})
        self.assertIsNone(evaluate(config, ctx))

    def test_AC021_env_file_deny(self):
        """read: .env ファイル → deny"""
        config = _make_config(
            read_rules=[_deny_rule("r1", path_patterns=["**/.env"])]
        )
        ctx = MatchContext(tool_name="read_file", tool_input={"filePath": ".env"})
        result = evaluate(config, ctx)
        self.assertIsNotNone(result)
        self.assertEqual(result.rule.action, "deny")

    def test_AC022_list_dir_no_match(self):
        """read: list_dir — ディレクトリパスがパターン不一致 → None"""
        config = _make_config(
            read_rules=[_deny_rule("r1", path_patterns=["docs/secrets/**"])]
        )
        ctx = MatchContext(tool_name="list_dir", tool_input={"path": "docs/secrets"})
        # "docs/secrets" は "docs/secrets/**" にマッチしない（末尾スラッシュなし）
        self.assertIsNone(evaluate(config, ctx))

    def test_AC023_empty_path_patterns_matches_all(self):
        """read: path_patterns 未指定 → 全ファイルにマッチ"""
        config = _make_config(
            read_rules=[_deny_rule("r1", path_patterns=[])]
        )
        ctx = MatchContext(tool_name="read_file", tool_input={"filePath": "any/file.txt"})
        result = evaluate(config, ctx)
        self.assertIsNotNone(result)
        self.assertEqual(result.rule.action, "deny")


# ---------------------------------------------------------------------------
# ac_rule_engine — command operations
# ---------------------------------------------------------------------------

class TestEvaluateCommandRules(unittest.TestCase):

    def test_AC030_no_rules_allows(self):
        """command: ルールなし → None"""
        config = _make_config()
        ctx = MatchContext(tool_name="run_in_terminal", tool_input={"command": "ls"})
        self.assertIsNone(evaluate(config, ctx))

    def test_AC031_destructive_command_deny(self):
        """command: rm -rf → deny"""
        config = _make_config(
            command_rules=[_deny_rule("r1", command_patterns=["rm -rf"])]
        )
        ctx = MatchContext(
            tool_name="run_in_terminal",
            tool_input={"command": "rm -rf ./dist"},
        )
        result = evaluate(config, ctx)
        self.assertIsNotNone(result)
        self.assertEqual(result.rule.action, "deny")

    def test_AC032_case_insensitive_match(self):
        """command: パターンマッチは大小文字無視"""
        config = _make_config(
            command_rules=[_deny_rule("r1", command_patterns=["rm -rf"])]
        )
        ctx = MatchContext(
            tool_name="run_in_terminal",
            tool_input={"command": "RM -RF ./dist"},
        )
        result = evaluate(config, ctx)
        self.assertIsNotNone(result)

    def test_AC033_command_no_match_allows(self):
        """command: パターン不一致 → None"""
        config = _make_config(
            command_rules=[_deny_rule("r1", command_patterns=["rm -rf"])]
        )
        ctx = MatchContext(tool_name="run_in_terminal", tool_input={"command": "git status"})
        self.assertIsNone(evaluate(config, ctx))

    def test_AC034_confirm_command(self):
        """command: git push --force → confirm"""
        config = _make_config(
            command_rules=[_confirm_rule("r1", command_patterns=["git push --force"])]
        )
        ctx = MatchContext(
            tool_name="run_in_terminal",
            tool_input={"command": "git push --force origin main"},
        )
        result = evaluate(config, ctx)
        self.assertIsNotNone(result)
        self.assertEqual(result.rule.action, "confirm")

    def test_AC035_empty_command_patterns_matches_all(self):
        """command: command_patterns 未指定 → 全コマンドにマッチ"""
        config = _make_config(
            command_rules=[_deny_rule("r1", command_patterns=[])]
        )
        ctx = MatchContext(
            tool_name="run_in_terminal",
            tool_input={"command": "any command"},
        )
        result = evaluate(config, ctx)
        self.assertIsNotNone(result)


# ---------------------------------------------------------------------------
# ac_rule_engine — 未分類ツール
# ---------------------------------------------------------------------------

class TestUnknownTools(unittest.TestCase):

    def test_AC040_semantic_search_allows(self):
        """未分類ツール semantic_search → None"""
        config = _make_config(
            write_rules=[_deny_rule("r1", path_patterns=["**"])],
        )
        ctx = MatchContext(tool_name="semantic_search", tool_input={"query": "test"})
        self.assertIsNone(evaluate(config, ctx))

    def test_AC041_grep_search_allows(self):
        """未分類ツール grep_search → None"""
        config = _make_config(
            write_rules=[_deny_rule("r1", path_patterns=["**"])],
        )
        ctx = MatchContext(tool_name="grep_search", tool_input={"query": "test"})
        self.assertIsNone(evaluate(config, ctx))


# ---------------------------------------------------------------------------
# パス正規化
# ---------------------------------------------------------------------------

class TestPathNormalization(unittest.TestCase):

    def test_AC050_windows_absolute_path_relative(self):
        """Windows絶対パス → cwd で相対化 → docs/** にマッチ"""
        config = _make_config(
            write_rules=[_deny_rule("r1", path_patterns=["docs/**"])]
        )
        ctx = MatchContext(
            tool_name="create_file",
            tool_input={"filePath": r"C:\GHC\docs\foo.md"},
            cwd=r"C:\GHC",
        )
        result = evaluate(config, ctx)
        self.assertIsNotNone(result)
        self.assertEqual(result.rule.action, "deny")

    def test_AC051_path_outside_cwd_no_match(self):
        """cwd外の絶対パス → 相対化されず docs/** にマッチしない"""
        config = _make_config(
            write_rules=[_deny_rule("r1", path_patterns=["docs/**"])]
        )
        ctx = MatchContext(
            tool_name="create_file",
            tool_input={"filePath": r"D:\other\docs\foo.md"},
            cwd=r"C:\GHC",
        )
        result = evaluate(config, ctx)
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# 有効/無効制御
# ---------------------------------------------------------------------------

class TestEnabledDisable(unittest.TestCase):

    def test_AC008_global_enabled_false_allows(self):
        """グローバル enabled=False → 全ルール無効 → None"""
        deny = _deny_rule("r1", path_patterns=["docs/**"])
        config = _make_config(enabled=False, write_rules=[deny])
        ctx = MatchContext(tool_name="create_file", tool_input={"filePath": "docs/foo.md"})
        self.assertIsNone(evaluate(config, ctx))

    def test_AC060_write_group_disabled_allows(self):
        """write_rules.enabled=False → write ルール無効 → None"""
        deny = _deny_rule("r1", path_patterns=["docs/**"])
        config = _make_config(write_enabled=False, write_rules=[deny])
        ctx = MatchContext(tool_name="create_file", tool_input={"filePath": "docs/foo.md"})
        self.assertIsNone(evaluate(config, ctx))

    def test_AC061_read_group_disabled_allows(self):
        """read_rules.enabled=False → read ルール無効 → None"""
        deny = _deny_rule("r1", path_patterns=["**/.env"])
        config = _make_config(read_enabled=False, read_rules=[deny])
        ctx = MatchContext(tool_name="read_file", tool_input={"filePath": ".env"})
        self.assertIsNone(evaluate(config, ctx))

    def test_AC062_command_group_disabled_allows(self):
        """command_rules.enabled=False → command ルール無効 → None"""
        deny = _deny_rule("r1", command_patterns=["rm -rf"])
        config = _make_config(command_enabled=False, command_rules=[deny])
        ctx = MatchContext(tool_name="run_in_terminal", tool_input={"command": "rm -rf ./dist"})
        self.assertIsNone(evaluate(config, ctx))


# ---------------------------------------------------------------------------
# access_control.py helper function tests
# ---------------------------------------------------------------------------

def _make_mock_event() -> MagicMock:
    """PreToolUsePayload のモックを返す。warn=0, deny=2, ask=0 を返す。"""
    event = MagicMock(spec=PreToolUsePayload)
    event.warn.return_value = 0
    event.deny.return_value = 2
    event.ask.return_value = 0
    return event


def _deny_rule_match(rule_id: str = "r1", path: str = "docs/foo.md") -> RuleMatch:
    return RuleMatch(
        rule=Rule(rule_id=rule_id, action="deny", when=WhenClause()),
        matched_values=[path],
    )


def _confirm_rule_match(rule_id: str = "r1") -> RuleMatch:
    return RuleMatch(
        rule=Rule(rule_id=rule_id, action="confirm", when=WhenClause()),
        matched_values=[],
    )


def _allow_rule_match(rule_id: str = "r1") -> RuleMatch:
    return RuleMatch(
        rule=Rule(rule_id=rule_id, action="allow", when=WhenClause()),
        matched_values=[],
    )


class TestBuildConfigWarning(unittest.TestCase):

    def test_AC080_empty_skipped_rules_returns_empty_string(self):
        """_build_config_warning: skipped_rules 空 → ''"""
        config = MagicMock()
        config.skipped_rules = []
        self.assertEqual(_build_config_warning(config), "")

    def test_AC081_skipped_rules_returns_warning_string(self):
        """_build_config_warning: skipped_rules あり → '⚠' で始まる文字列"""
        config = MagicMock()
        config.skipped_rules = ["bad-rule: invalid action 'hack'"]
        result = _build_config_warning(config)
        self.assertTrue(result.startswith("⚠"))
        self.assertIn("bad-rule", result)


class TestLoadConfigOrExit(unittest.TestCase):

    def test_AC082_file_not_found_exits_with_warn(self):
        """_load_config_or_exit: FileNotFoundError → event.warn() 呼び出し後 sys.exit(0)"""
        event = _make_mock_event()
        with patch("access_control.load_config", side_effect=FileNotFoundError):
            with self.assertRaises(SystemExit) as ctx:
                _load_config_or_exit(event, Path("nonexistent.json"))
        self.assertEqual(ctx.exception.code, 0)
        event.warn.assert_called_once()

    def test_AC083_parse_error_exits_with_warn(self):
        """_load_config_or_exit: Exception → event.warn() 呼び出し後 sys.exit(0)"""
        event = _make_mock_event()
        with patch("access_control.load_config", side_effect=Exception("parse failed")):
            with self.assertRaises(SystemExit) as ctx:
                _load_config_or_exit(event, Path("bad.json"))
        self.assertEqual(ctx.exception.code, 0)
        event.warn.assert_called_once()
        self.assertIn("parse failed", event.warn.call_args[0][0])

    def test_AC084_valid_config_returns_config(self):
        """_load_config_or_exit: 正常 → config を返す（sys.exit なし）"""
        event = _make_mock_event()
        expected = MagicMock()
        with patch("access_control.load_config", return_value=expected):
            result = _load_config_or_exit(event, Path("ok.json"))
        self.assertIs(result, expected)
        event.warn.assert_not_called()


class TestDispatchAction(unittest.TestCase):

    def test_AC085_none_result_no_warning_does_nothing(self):
        """_dispatch_action: result=None + config_warning='' → sys.exit なし"""
        event = _make_mock_event()
        _dispatch_action(event, None, "")
        event.warn.assert_not_called()
        event.deny.assert_not_called()
        event.ask.assert_not_called()

    def test_AC086_none_result_with_warning_exits_warn(self):
        """_dispatch_action: result=None + config_warning あり → sys.exit(warn)"""
        event = _make_mock_event()
        with self.assertRaises(SystemExit) as ctx:
            _dispatch_action(event, None, "⚠ bad rules")
        self.assertEqual(ctx.exception.code, 0)
        event.warn.assert_called_once_with("⚠ bad rules")

    def test_AC087_deny_action_exits_deny(self):
        """_dispatch_action: action='deny' → sys.exit(deny) / exit code 2"""
        event = _make_mock_event()
        with self.assertRaises(SystemExit) as ctx:
            _dispatch_action(event, _deny_rule_match(), "")
        self.assertEqual(ctx.exception.code, 2)
        event.deny.assert_called_once()

    def test_AC088_deny_action_with_warning_appends_warning_to_reason(self):
        """_dispatch_action: action='deny' + config_warning → reason に warning を含む"""
        event = _make_mock_event()
        with self.assertRaises(SystemExit):
            _dispatch_action(event, _deny_rule_match(), "⚠ bad rules")
        reason_arg = event.deny.call_args[0][0]
        self.assertIn("⚠ bad rules", reason_arg)

    def test_AC089_confirm_action_exits_ask(self):
        """_dispatch_action: action='confirm' → sys.exit(ask) / exit code 0"""
        event = _make_mock_event()
        with self.assertRaises(SystemExit) as ctx:
            _dispatch_action(event, _confirm_rule_match(), "")
        self.assertEqual(ctx.exception.code, 0)
        event.ask.assert_called_once()

    def test_AC090_allow_action_no_warning_does_nothing(self):
        """_dispatch_action: action='allow' + config_warning='' → sys.exit なし"""
        event = _make_mock_event()
        _dispatch_action(event, _allow_rule_match(), "")
        event.warn.assert_not_called()
        event.deny.assert_not_called()
        event.ask.assert_not_called()

    def test_AC091_allow_action_with_warning_exits_warn_regression(self):
        """_dispatch_action: action='allow' + config_warning あり → sys.exit(warn) [リグレッション]"""
        event = _make_mock_event()
        with self.assertRaises(SystemExit) as ctx:
            _dispatch_action(event, _allow_rule_match(), "⚠ bad rules")
        self.assertEqual(ctx.exception.code, 0)
        event.warn.assert_called_once_with("⚠ bad rules")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
