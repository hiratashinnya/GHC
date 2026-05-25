#!/usr/bin/env python3
"""Unit tests for ac_config_loader.py and ac_rule_engine.py"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

LOCAL_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / ".github" / "hooks" / "scripts"
SCRIPTS_DIR = LOCAL_SCRIPTS_DIR if LOCAL_SCRIPTS_DIR.is_dir() else Path(r"c:\GHC\.github\hooks\scripts")
for relative in ("core", "access_control", "tooling", "shared", "entrypoints"):
    sys.path.insert(0, str(SCRIPTS_DIR / relative))

from ac_config_loader import (
    WhenClause,
    Rule,
    RuleGroup,
    AccessControlConfig,
    WhitelistConfig,
    WhitelistRule,
    WhitelistRuleGroup,
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
from tool_input_parser import get_write_paths, get_read_paths, get_command_string


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
    whitelist=None,
) -> AccessControlConfig:
    return AccessControlConfig(
        enabled=enabled,
        write_rules=RuleGroup(enabled=write_enabled, rules=write_rules or []),
        read_rules=RuleGroup(enabled=read_enabled, rules=read_rules or []),
        command_rules=RuleGroup(enabled=command_enabled, rules=command_rules or []),
        whitelist=whitelist or WhitelistConfig(),
    )


def _deny_rule(rule_id: str, path_patterns=None, command_patterns=None, scope_patterns=None) -> Rule:
    return Rule(
        rule_id=rule_id,
        action="deny",
        when=WhenClause(
            path_patterns=path_patterns or [],
            command_patterns=command_patterns or [],
            scope_patterns=scope_patterns or [],
        ),
    )


def _confirm_rule(rule_id: str, path_patterns=None, command_patterns=None, scope_patterns=None) -> Rule:
    return Rule(
        rule_id=rule_id,
        action="confirm",
        when=WhenClause(
            path_patterns=path_patterns or [],
            command_patterns=command_patterns or [],
            scope_patterns=scope_patterns or [],
        ),
    )


def _disabled_rule(rule_id: str, path_patterns=None) -> Rule:
    return Rule(
        rule_id=rule_id,
        action="disabled",
        when=WhenClause(path_patterns=path_patterns or []),
    )


def _whitelist_rule(
    rule_id: str,
    path_patterns=None,
    command_patterns=None,
    scope_patterns=None,
    arbitration="blacklist",
    enabled=True,
) -> WhitelistRule:
    return WhitelistRule(
        rule_id=rule_id,
        arbitration=arbitration,
        enabled=enabled,
        when=WhenClause(
            path_patterns=path_patterns or [],
            command_patterns=command_patterns or [],
            scope_patterns=scope_patterns or [],
        ),
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

    def test_AC008a_parse_when_scope_patterns(self):
        """_parse_when: scope_patterns を正しく格納する"""
        data = {
            "read_rules": [
                {"id": "r1", "action": "deny", "when": {"scope_patterns": ["**/.env"]}}
            ]
        }
        path = _write_config(self.tmppath, data)
        config = load_config(path)
        self.assertEqual(config.read_rules.rules[0].when.scope_patterns, ["**/.env"])

    def test_AC008b_parse_when_path_and_scope_patterns(self):
        """_parse_when: path_patterns と scope_patterns の両方を正しく格納する"""
        data = {
            "read_rules": [
                {
                    "id": "r1",
                    "action": "deny",
                    "when": {
                        "path_patterns": ["docs/**"],
                        "scope_patterns": ["docs/**"],
                    },
                }
            ]
        }
        path = _write_config(self.tmppath, data)
        config = load_config(path)
        self.assertEqual(config.read_rules.rules[0].when.path_patterns, ["docs/**"])
        self.assertEqual(config.read_rules.rules[0].when.scope_patterns, ["docs/**"])

    def test_AC200_parse_whitelist_global_group_and_item(self):
        """whitelist: global/group/item 設定が読み込まれる"""
        data = {
            "whitelist": {
                "enabled": True,
                "arbitration": "whitelist",
                "write_rules": {
                    "enabled": True,
                    "arbitration": "confirm",
                    "rules": [
                        {
                            "id": "w1",
                            "arbitration": "blacklist",
                            "when": {"path_patterns": ["docs/**"]},
                        }
                    ],
                },
            }
        }
        path = _write_config(self.tmppath, data)
        config = load_config(path)
        self.assertTrue(config.whitelist.enabled)
        self.assertEqual(config.whitelist.arbitration, "whitelist")
        self.assertEqual(config.whitelist.write_rules.arbitration, "confirm")
        self.assertEqual(config.whitelist.write_rules.rules[0].arbitration, "blacklist")

    def test_AC201_parse_whitelist_arbitration_fallback_with_warning(self):
        """whitelist: 不正 arbitration は blacklist にフォールバックし warning 収集"""
        data = {
            "whitelist": {
                "enabled": True,
                "arbitration": "invalid",
            }
        }
        path = _write_config(self.tmppath, data)
        config = load_config(path)
        self.assertEqual(config.whitelist.arbitration, "blacklist")
        self.assertTrue(any("arbitration" in warning for warning in config.skipped_rules))


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

    def test_AC202_whitelist_blacklist_priority_keeps_deny(self):
        """write: whitelist arbitration=blacklist は deny を維持"""
        whitelist = WhitelistConfig(
            enabled=True,
            write_rules=WhitelistRuleGroup(
                rules=[
                    _whitelist_rule(
                        "w1",
                        path_patterns=["docs/**"],
                        arbitration="blacklist",
                    )
                ]
            ),
        )
        config = _make_config(
            write_rules=[_deny_rule("r1", path_patterns=["docs/**"])],
            whitelist=whitelist,
        )
        ctx = MatchContext(tool_name="create_file", tool_input={"filePath": "docs/foo.md"})
        result = evaluate(config, ctx)
        self.assertIsNotNone(result)
        self.assertEqual(result.rule.action, "deny")

    def test_AC203_whitelist_confirm_demotes_deny_to_confirm(self):
        """write: whitelist arbitration=confirm は deny を confirm に調停"""
        whitelist = WhitelistConfig(
            enabled=True,
            write_rules=WhitelistRuleGroup(
                rules=[
                    _whitelist_rule(
                        "w1",
                        path_patterns=["docs/**"],
                        arbitration="confirm",
                    )
                ]
            ),
        )
        config = _make_config(
            write_rules=[_deny_rule("r1", path_patterns=["docs/**"])],
            whitelist=whitelist,
        )
        ctx = MatchContext(tool_name="create_file", tool_input={"filePath": "docs/foo.md"})
        result = evaluate(config, ctx)
        self.assertIsNotNone(result)
        self.assertEqual(result.rule.action, "confirm")

    def test_AC204_whitelist_priority_allows_despite_blacklist(self):
        """write: whitelist arbitration=whitelist は blacklist を無効化して allow"""
        whitelist = WhitelistConfig(
            enabled=True,
            write_rules=WhitelistRuleGroup(
                rules=[
                    _whitelist_rule(
                        "w1",
                        path_patterns=["docs/**"],
                        arbitration="whitelist",
                    )
                ]
            ),
        )
        config = _make_config(
            write_rules=[_deny_rule("r1", path_patterns=["docs/**"])],
            whitelist=whitelist,
        )
        ctx = MatchContext(tool_name="create_file", tool_input={"filePath": "docs/foo.md"})
        self.assertIsNone(evaluate(config, ctx))

    def test_AC205_whitelist_multi_match_prefers_blacklist_priority(self):
        """write: whitelist 複数マッチ時は blacklist > confirm > whitelist 優先"""
        whitelist = WhitelistConfig(
            enabled=True,
            write_rules=WhitelistRuleGroup(
                rules=[
                    _whitelist_rule("w1", path_patterns=["docs/**"], arbitration="whitelist"),
                    _whitelist_rule("w2", path_patterns=["docs/**"], arbitration="confirm"),
                    _whitelist_rule("w3", path_patterns=["docs/**"], arbitration="blacklist"),
                ]
            ),
        )
        config = _make_config(
            write_rules=[_deny_rule("r1", path_patterns=["docs/**"])],
            whitelist=whitelist,
        )
        ctx = MatchContext(tool_name="create_file", tool_input={"filePath": "docs/foo.md"})
        result = evaluate(config, ctx)
        self.assertIsNotNone(result)
        self.assertEqual(result.rule.action, "deny")

    def test_AC206_whitelist_global_enabled_false_skips_matching(self):
        """write: whitelist enabled=false は whitelist 評価をスキップする"""
        whitelist = WhitelistConfig(
            enabled=False,
            write_rules=WhitelistRuleGroup(
                rules=[
                    _whitelist_rule("w1", path_patterns=["docs/**"], arbitration="whitelist"),
                ]
            ),
        )
        config = _make_config(
            write_rules=[_deny_rule("r1", path_patterns=["docs/**"])],
            whitelist=whitelist,
        )
        ctx = MatchContext(tool_name="create_file", tool_input={"filePath": "docs/foo.md"})
        result = evaluate(config, ctx)
        self.assertIsNotNone(result)
        self.assertEqual(result.rule.action, "deny")

    def test_AC207_whitelist_group_enabled_false_skips_matching(self):
        """write: whitelist write_rules.enabled=false は操作タイプ単位でスキップ"""
        whitelist = WhitelistConfig(
            enabled=True,
            write_rules=WhitelistRuleGroup(
                enabled=False,
                rules=[
                    _whitelist_rule("w1", path_patterns=["docs/**"], arbitration="whitelist"),
                ],
            ),
        )
        config = _make_config(
            write_rules=[_deny_rule("r1", path_patterns=["docs/**"])],
            whitelist=whitelist,
        )
        ctx = MatchContext(tool_name="create_file", tool_input={"filePath": "docs/foo.md"})
        result = evaluate(config, ctx)
        self.assertIsNotNone(result)
        self.assertEqual(result.rule.action, "deny")

    def test_AC208_whitelist_item_enabled_false_skips_item(self):
        """write: whitelist rule.enabled=false の項目は評価対象外"""
        whitelist = WhitelistConfig(
            enabled=True,
            write_rules=WhitelistRuleGroup(
                rules=[
                    _whitelist_rule(
                        "w1",
                        path_patterns=["docs/**"],
                        arbitration="whitelist",
                        enabled=False,
                    )
                ]
            ),
        )
        config = _make_config(
            write_rules=[_deny_rule("r1", path_patterns=["docs/**"])],
            whitelist=whitelist,
        )
        ctx = MatchContext(tool_name="create_file", tool_input={"filePath": "docs/foo.md"})
        result = evaluate(config, ctx)
        self.assertIsNotNone(result)
        self.assertEqual(result.rule.action, "deny")


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

    def test_AC140_scope_definite_inclusion_global_search_deny(self):
        """read: global grep scope definitely includes protected env files → deny"""
        config = _make_config(
            read_rules=[_deny_rule("r1", scope_patterns=["**/.env"])]
        )
        ctx = MatchContext(tool_name="grep_search", tool_input={"includePattern": "**/*"})
        result = evaluate(config, ctx)
        self.assertIsNotNone(result)
        self.assertEqual(result.rule.action, "deny")

    def test_AC141_scope_parent_subtree_deny(self):
        """read: parent subtree grep definitely includes child protected subtree → deny"""
        config = _make_config(
            read_rules=[_deny_rule("r1", scope_patterns=[".github/hooks/**"])]
        )
        ctx = MatchContext(tool_name="grep_search", tool_input={"includePattern": ".github/**"})
        result = evaluate(config, ctx)
        self.assertIsNotNone(result)
        self.assertEqual(result.rule.action, "deny")

    def test_AC142_scope_uncertain_overlap_confirm(self):
        """read: wider src grep with narrower env rule is uncertain overlap → confirm"""
        config = _make_config(
            read_rules=[_confirm_rule("r1", scope_patterns=["src/**/*.env"])]
        )
        ctx = MatchContext(tool_name="grep_search", tool_input={"includePattern": "src/**"})
        result = evaluate(config, ctx)
        self.assertIsNotNone(result)
        self.assertEqual(result.rule.action, "confirm")

    def test_AC143_scope_definite_disjoint_allows(self):
        """read: disjoint grep scope does not match protected scopes"""
        config = _make_config(
            read_rules=[
                _deny_rule("r1", scope_patterns=["**/.env"]),
                _confirm_rule("r2", scope_patterns=[".github/**"]),
            ]
        )
        ctx = MatchContext(tool_name="grep_search", tool_input={"includePattern": "docs/**"})
        self.assertIsNone(evaluate(config, ctx))

    def test_AC144_ambiguous_empty_include_pattern_confirm(self):
        """read: empty grep includePattern is treated as ambiguous and defaults to confirm"""
        config = _make_config(
            read_rules=[_confirm_rule("r1", scope_patterns=["**/.env"])]
        )
        ctx = MatchContext(tool_name="grep_search", tool_input={"includePattern": ""})
        result = evaluate(config, ctx)
        self.assertIsNotNone(result)
        self.assertEqual(result.rule.action, "confirm")

    def test_AC145_file_search_global_scope_deny(self):
        """read: file_search global query definitely includes protected secret files → deny"""
        config = _make_config(
            read_rules=[_deny_rule("r1", scope_patterns=["**/*.secret"])]
        )
        ctx = MatchContext(tool_name="file_search", tool_input={"query": "**/*"})
        result = evaluate(config, ctx)
        self.assertIsNotNone(result)
        self.assertEqual(result.rule.action, "deny")

    def test_AC146_concrete_path_match_has_priority(self):
        """read: concrete path match still wins immediately even if scope patterns also exist"""
        config = _make_config(
            read_rules=[_deny_rule("r1", path_patterns=["**/.env"], scope_patterns=["**/*.env"])]
        )
        ctx = MatchContext(tool_name="read_file", tool_input={"filePath": ".env"})
        result = evaluate(config, ctx)
        self.assertIsNotNone(result)
        self.assertEqual(result.rule.action, "deny")

    def test_AC147_scope_fallback_to_path_patterns_for_backward_compat(self):
        """read: scope_patterns omitted falls back to path_patterns for search scope evaluation"""
        config = _make_config(
            read_rules=[_deny_rule("r1", path_patterns=["**/.env"])]
        )
        ctx = MatchContext(tool_name="grep_search", tool_input={"includePattern": ".env"})
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

    def test_AC034_force_push_deny(self):
        """command: git push --force → deny"""
        config = _make_config(
            command_rules=[_deny_rule("r1", command_patterns=["git push --force"])]
        )
        ctx = MatchContext(
            tool_name="run_in_terminal",
            tool_input={"command": "git push --force origin main"},
        )
        result = evaluate(config, ctx)
        self.assertIsNotNone(result)
        self.assertEqual(result.rule.action, "deny")

    def test_AC036_imported_dangerous_patterns_deny(self):
        """command: settings false 由来の代表パターンが deny になる"""
        patterns = [
            "curl ",
            "Invoke-WebRequest",
            "taskkill",
            "chmod ",
            "Invoke-Expression",
            "git reset --hard",
            " -delete",
            "rg --pre",
            "sed --expression",
            "sort -o",
            "tree -o",
        ]
        config = _make_config(command_rules=[_deny_rule("r1", command_patterns=patterns)])
        commands = [
            "curl https://example.com",
            "Invoke-WebRequest https://example.com",
            "taskkill /IM node.exe /F",
            "chmod 755 script.sh",
            "Invoke-Expression \"Write-Host test\"",
            "git reset --hard HEAD~1",
            "find . -delete",
            "rg --pre ./preprocessor.cmd pattern",
            "sed --expression s/a/b/ file.txt",
            "sort -o out.txt in.txt",
            "tree -o tree.txt",
        ]
        for command in commands:
            with self.subTest(command=command):
                ctx = MatchContext(tool_name="run_in_terminal", tool_input={"command": command})
                result = evaluate(config, ctx)
                self.assertIsNotNone(result)
                self.assertEqual(result.rule.action, "deny")

    def test_AC038_package_install_deny(self):
        """command: pip/conda/poetry install → deny"""
        patterns = [
            "pip install",
            "pip3 install",
            "conda install",
            "poetry add",
            "pipenv install",
            "pipx install",
        ]
        config = _make_config(command_rules=[_deny_rule("r1", command_patterns=patterns)])
        commands = [
            "pip install requests",
            "pip3 install numpy",
            "conda install pandas",
            "poetry add fastapi",
            "pipenv install flask",
            "pipx install black",
        ]
        for command in commands:
            with self.subTest(command=command):
                ctx = MatchContext(tool_name="run_in_terminal", tool_input={"command": command})
                result = evaluate(config, ctx)
                self.assertIsNotNone(result)
                self.assertEqual(result.rule.action, "deny")

    def test_AC039_git_push_clone_deny(self):
        """command: git push / git clone → deny"""
        config = _make_config(
            command_rules=[_deny_rule("r1", command_patterns=["git push ", "git clone"])]
        )
        commands = [
            "git push origin main",
            "git push --force origin main",
            "git clone https://github.com/example/repo.git",
            "git clone git@github.com:example/repo.git",
        ]
        for command in commands:
            with self.subTest(command=command):
                ctx = MatchContext(tool_name="run_in_terminal", tool_input={"command": command})
                result = evaluate(config, ctx)
                self.assertIsNotNone(result)
                self.assertEqual(result.rule.action, "deny")

    def test_AC042_powershell_linux_install_deny(self):
        """command: PowerShell/Linux/Node package install commands → deny"""
        patterns = [
            "Install-Module",
            "Install-Package",
            "winget install",
            "choco install",
            "scoop install",
            "apt install",
            "apt-get install",
            "yum install",
            "dnf install",
            "pacman -S",
            "zypper install",
            "apk add",
            "brew install",
            "snap install",
            "npm install",
            "yarn add",
            "pnpm add",
        ]
        config = _make_config(command_rules=[_deny_rule("r1", command_patterns=patterns)])
        commands = [
            "Install-Module Pester",
            "Install-Package Pester",
            "winget install Git.Git",
            "choco install git",
            "scoop install git",
            "apt install git",
            "apt-get install git",
            "yum install git",
            "dnf install git",
            "pacman -S git",
            "zypper install git",
            "apk add git",
            "brew install git",
            "snap install code",
            "npm install lodash",
            "yarn add react",
            "pnpm add axios",
        ]
        for command in commands:
            with self.subTest(command=command):
                ctx = MatchContext(tool_name="run_in_terminal", tool_input={"command": command})
                result = evaluate(config, ctx)
                self.assertIsNotNone(result)
                self.assertEqual(result.rule.action, "deny")

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
# Command pattern regex matching tests
# ---------------------------------------------------------------------------

class TestCommandPatternRegex(unittest.TestCase):
    """Tests for _match_command_patterns with regex support"""

    def test_AC092_git_add_no_false_positive_with_dd_word_boundary(self):
        """AC-092: "git add file.txt" should not match \\bdd\\b pattern (word boundary precision)"""
        patterns = [r"\bdd\b", r"\brm\b"]
        command = "git add file.txt"
        matched = _match_command_patterns(patterns, command, debug=None)
        self.assertEqual(matched, [])

    def test_AC093_dd_command_matches_word_boundary_pattern(self):
        """AC-093: "dd if=/dev/zero" should match \\bdd\\b pattern"""
        patterns = [r"\bdd\b"]
        command = "dd if=/dev/zero"
        matched = _match_command_patterns(patterns, command, debug=None)
        self.assertEqual(matched, [r"\bdd\b"])

    def test_AC093b_deadline_not_match_dd_word_boundary(self):
        """AC-093b: "deadline-2026-01-01" should NOT match \\bdd\\b (word boundary prevents substring match)"""
        patterns = [r"\bdd\b"]
        command = "deadline-2026-01-01"
        matched = _match_command_patterns(patterns, command, debug=None)
        self.assertEqual(matched, [])

    def test_AC094_invalid_regex_skipped_and_logged(self):
        """AC-094: Invalid regex patterns are skipped; errors logged to debug.log"""
        patterns = [r"\bdd\b", r"[invalid(regex"]
        command = "rm -rf"
        mock_debug = MagicMock()
        matched = _match_command_patterns(patterns, command, debug=mock_debug)
        # Only valid pattern is processed; invalid one triggers debug log call
        self.assertNotIn(r"[invalid(regex", matched)
        mock_debug.log.assert_called_once()
        call_args = mock_debug.log.call_args
        self.assertEqual(call_args[1].get("log_type"), "regex_error")

    def test_AC095_multiple_patterns_all_matches_returned(self):
        """AC-095: Multiple matching patterns all returned in result"""
        patterns = [r"\brm\b", r"\bdd\b", "dev-null"]
        command = "rm -rf ./dist"
        matched = _match_command_patterns(patterns, command, debug=None)
        self.assertIn(r"\brm\b", matched)
        self.assertNotIn(r"\bdd\b", matched)
        self.assertNotIn("dev-null", matched)

    def test_AC096_case_insensitive_regex_match(self):
        """AC-096: Regex matching is case-insensitive (IGNORECASE)"""
        patterns = [r"\bDD\b"]
        command = "dd if=/dev/zero"
        matched = _match_command_patterns(patterns, command, debug=None)
        self.assertEqual(matched, [r"\bDD\b"])


# ---------------------------------------------------------------------------
# tool_input_parser — get_write_paths
# ---------------------------------------------------------------------------

class TestGetWritePaths(unittest.TestCase):

    def test_AC100_apply_patch_update_file(self):
        """AC-100: apply_patch extracts path from '*** Update File:' line"""
        tool_input = {"input": "*** Update File: c:\\GHC\\docs\\foo.md\n@@\n-old\n+new"}
        result = get_write_paths("apply_patch", tool_input)
        self.assertEqual(result, ["c:\\GHC\\docs\\foo.md"])

    def test_AC101_apply_patch_multiple_files(self):
        """AC-101: apply_patch extracts multiple paths"""
        patch = "*** Update File: docs/foo.md\n@@\n*** Add File: src/bar.py\n@@"
        result = get_write_paths("apply_patch", {"input": patch})
        self.assertEqual(result, ["docs/foo.md", "src/bar.py"])

    def test_AC102_apply_patch_rename_source_only(self):
        """AC-102: apply_patch rename patch returns source path only"""
        patch = "*** Update File: old.py -> new.py"
        result = get_write_paths("apply_patch", {"input": patch})
        self.assertEqual(result, ["old.py"])

    def test_AC103_apply_patch_invalid_input_type(self):
        """AC-103: apply_patch with non-string input returns []"""
        result = get_write_paths("apply_patch", {"input": 42})
        self.assertEqual(result, [])

    def test_AC104_create_directory_dir_path(self):
        """AC-104: create_directory returns dirPath"""
        result = get_write_paths("create_directory", {"dirPath": "src/subdir"})
        self.assertEqual(result, ["src/subdir"])

    def test_AC105_non_write_tool_returns_empty(self):
        """AC-105: non-write tool returns []"""
        result = get_write_paths("read_file", {"filePath": "docs/foo.md"})
        self.assertEqual(result, [])


# ---------------------------------------------------------------------------
# tool_input_parser — get_read_paths
# ---------------------------------------------------------------------------

class TestGetReadPaths(unittest.TestCase):

    def test_AC110_read_file_filepath(self):
        """AC-110: read_file returns filePath"""
        result = get_read_paths("read_file", {"filePath": "docs/foo.md"})
        self.assertEqual(result, ["docs/foo.md"])

    def test_AC111_get_errors_file_paths(self):
        """AC-111: get_errors returns filePaths list"""
        result = get_read_paths("get_errors", {"filePaths": ["a.py", "b.py"]})
        self.assertEqual(result, ["a.py", "b.py"])

    def test_AC112_grep_search_include_pattern(self):
        """AC-112: grep_search returns includePattern"""
        result = get_read_paths("grep_search", {"includePattern": "src/**/*.py"})
        self.assertEqual(result, ["src/**/*.py"])

    def test_AC113_non_read_tool_returns_empty(self):
        """AC-113: non-read tool (apply_patch) returns []"""
        result = get_read_paths("apply_patch", {"input": "*** Update File: foo.py"})
        self.assertEqual(result, [])


# ---------------------------------------------------------------------------
# tool_input_parser — get_command_string
# ---------------------------------------------------------------------------

class TestGetCommandString(unittest.TestCase):

    def test_AC120_command_key_direct(self):
        """AC-120: direct command key"""
        result = get_command_string({"command": "git status"})
        self.assertEqual(result, "git status")

    def test_AC121_create_and_run_task_command_args(self):
        """AC-121: task.command + task.args are concatenated"""
        result = get_command_string({"task": {"command": "python", "args": ["-m", "pytest"]}})
        self.assertEqual(result, "python -m pytest")

    def test_AC122_task_empty_args(self):
        """AC-122: task.args empty returns command only"""
        result = get_command_string({"task": {"command": "python", "args": []}})
        self.assertEqual(result, "python")

    def test_AC123_empty_input_returns_empty_string(self):
        """AC-123: no matching key returns empty string"""
        result = get_command_string({})
        self.assertEqual(result, "")


# ---------------------------------------------------------------------------
# ac_rule_engine — evaluate() via tool_input_parser
# ---------------------------------------------------------------------------

class TestEvaluateViaParser(unittest.TestCase):

    def _make_config(self, tmpdir, rules_by_group):
        data = {
            "enabled": True,
            "write_rules": {"enabled": True, "rules": rules_by_group.get("write", [])},
            "read_rules": {"enabled": True, "rules": rules_by_group.get("read", [])},
            "command_rules": {"enabled": True, "rules": rules_by_group.get("command", [])},
        }
        return _write_config(tmpdir, data)

    def test_AC130_apply_patch_path_deny(self):
        """AC-130: apply_patch path matches deny rule"""
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            config_path = self._make_config(tmpdir, {"write": [{
                "rule_id": "r1", "action": "deny",
                "when": {"path_patterns": [".github/hooks/scripts/**"]},
            }]})
            from ac_config_loader import load_config
            config = load_config(config_path)
            patch = "*** Update File: c:\\GHC\\.github\\hooks\\scripts\\foo.py"
            ctx = MatchContext(
                tool_name="apply_patch",
                tool_input={"input": patch},
                cwd="c:\\GHC",
            )
            result = evaluate(config, ctx)
            self.assertIsNotNone(result)
            self.assertEqual(result.rule.action, "deny")

    def test_AC131_create_and_run_task_command_deny(self):
        """AC-131: create_and_run_task task.command+args matches deny rule"""
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            config_path = self._make_config(tmpdir, {"command": [{
                "rule_id": "r1", "action": "deny",
                "when": {"command_patterns": [r"\brm\b"]},
            }]})
            from ac_config_loader import load_config
            config = load_config(config_path)
            ctx = MatchContext(
                tool_name="create_and_run_task",
                tool_input={"task": {"command": "rm", "args": ["-rf", "./dist"]}},
                cwd="",
            )
            result = evaluate(config, ctx)
            self.assertIsNotNone(result)
            self.assertEqual(result.rule.action, "deny")

    def test_AC132_send_to_terminal_deny(self):
        """AC-132: send_to_terminal is evaluated as command tool"""
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            config_path = self._make_config(tmpdir, {"command": [{
                "rule_id": "r1", "action": "deny",
                "when": {"command_patterns": [r"\bgit\b\s+push\b"]},
            }]})
            from ac_config_loader import load_config
            config = load_config(config_path)
            ctx = MatchContext(
                tool_name="send_to_terminal",
                tool_input={"command": "git push origin main"},
                cwd="",
            )
            result = evaluate(config, ctx)
            self.assertIsNotNone(result)
            self.assertEqual(result.rule.action, "deny")

    def test_AC133_grep_search_include_pattern_no_match(self):
        """AC-133: grep_search includePattern '.env' matches '**/.env' and is denied"""
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            config_path = self._make_config(tmpdir, {"read": [{
                "rule_id": "r1", "action": "deny",
                "when": {"path_patterns": ["**/.env"]},
            }]})
            from ac_config_loader import load_config
            config = load_config(config_path)
            ctx = MatchContext(
                tool_name="grep_search",
                tool_input={"includePattern": ".env"},
                cwd="",
            )
            result = evaluate(config, ctx)
            self.assertIsNotNone(result)
            self.assertEqual(result.rule.action, "deny")

    def test_AC134_workspace_outside_absolute_path_deny(self):
        """AC-134: absolute path outside workspace is still evaluated (not dropped)"""
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            config_path = self._make_config(tmpdir, {"write": [{
                "rule_id": "r1", "action": "deny",
                "when": {"path_patterns": ["D:/other/**"]},
            }]})
            from ac_config_loader import load_config
            config = load_config(config_path)
            ctx = MatchContext(
                tool_name="create_file",
                tool_input={"filePath": "D:/other/secret.py"},
                cwd="C:/GHC",
            )
            result = evaluate(config, ctx)
            self.assertIsNotNone(result)
            self.assertEqual(result.rule.action, "deny")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
