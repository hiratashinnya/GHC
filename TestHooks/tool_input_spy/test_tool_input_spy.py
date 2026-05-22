#!/usr/bin/env python3
"""Unit tests for tool_input_spy.py"""

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

from tool_input_spy import _sanitize


class TestSanitize(unittest.TestCase):

    def test_SP001_short_string_unchanged(self):
        s = "x" * 100
        result = _sanitize(s)
        self.assertEqual(result, s)

    def test_SP002_long_string_truncated(self):
        s = "x" * 400
        result = _sanitize(s)
        self.assertTrue(isinstance(result, str))
        self.assertTrue(result.startswith("x" * 300))
        self.assertIn("[truncated 100 chars]", result)

    def test_SP003_dict_nested_truncation(self):
        d = {"key": "y" * 400}
        result = _sanitize(d)
        self.assertIn("[truncated", result["key"])

    def test_SP004_list_element_truncation(self):
        lst = ["z" * 400, "a" * 100]
        result = _sanitize(lst)
        self.assertIn("[truncated", result[0])
        self.assertEqual(result[1], "a" * 100)

    def test_SP007_non_string_dict_value_passthrough(self):
        result = _sanitize({"count": 42})
        self.assertEqual(result, {"count": 42})


class TestMain(unittest.TestCase):
    """Test main() — debug logging enabled/disabled."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmppath = Path(self._tmpdir.name)

    def tearDown(self):
        self._tmpdir.cleanup()

    def _make_stdin_mock(self, payload: dict):
        mock = MagicMock()
        mock.isatty.return_value = False
        mock.buffer.read.return_value = json.dumps(payload).encode("utf-8")
        return mock

    def _run_main_with_debug(self, enable: bool, payload: dict):
        if enable:
            flag = self.tmppath / "tool_input_spy.debug"
            flag.touch()
        with patch("hook_payload.sys.stdin", self._make_stdin_mock(payload)), \
             patch("tool_input_spy.SCRIPT_DIR", self.tmppath), \
             patch("tool_input_spy.DEBUG.flag_path", self.tmppath / "tool_input_spy.debug"), \
             patch("tool_input_spy.DEBUG.log_path", self.tmppath / "tool_input_spy.debug.log"), \
             patch("sys.argv", ["tool_input_spy.py", "--event", "PostToolUse"]):
            from tool_input_spy import main
            main()

    def test_SP005_debug_enabled_writes_log(self):
        payload = {
            "hookEventName": "PreToolUse",
            "tool_name": "read_file",
            "tool_input": {"filePath": "docs/x.md"},
        }
        self._run_main_with_debug(True, payload)
        log = self.tmppath / "tool_input_spy.debug.log"
        self.assertTrue(log.exists())
        content = log.read_text(encoding="utf-8")
        self.assertIn("spy", content)

    def test_SP006_debug_disabled_no_log(self):
        payload = {
            "hookEventName": "PreToolUse",
            "tool_name": "read_file",
            "tool_input": {"filePath": "docs/x.md"},
        }
        self._run_main_with_debug(False, payload)
        log = self.tmppath / "tool_input_spy.debug.log"
        self.assertFalse(log.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
