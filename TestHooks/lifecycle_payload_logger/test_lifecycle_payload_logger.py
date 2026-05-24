#!/usr/bin/env python3
"""Unit tests for lifecycle_payload_logger.py"""

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


class TestMain(unittest.TestCase):
    """Tests for main() in lifecycle_payload_logger — debug logging and event filtering."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmppath = Path(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _make_stdin_mock(self, payload: dict) -> MagicMock:
        mock = MagicMock()
        mock.isatty.return_value = False
        mock.buffer.read.return_value = json.dumps(payload).encode("utf-8")
        return mock

    def _run_main(self, enable_debug: bool, payload: dict) -> None:
        if enable_debug:
            flag = self.tmppath / "lifecycle_payload_logger.debug"
            flag.touch()
        with patch("hook_input.sys.stdin", self._make_stdin_mock(payload)), \
             patch("lifecycle_payload_logger.DEBUG.flag_path",
                   self.tmppath / "lifecycle_payload_logger.debug"), \
             patch("lifecycle_payload_logger.DEBUG.log_path",
                   self.tmppath / "lifecycle_payload_logger.debug.log"):
            from lifecycle_payload_logger import main
            main()

    def _log_content(self) -> str:
        log_path = self.tmppath / "lifecycle_payload_logger.debug.log"
        return log_path.read_text(encoding="utf-8") if log_path.exists() else ""

    def test_LC001_debug_disabled_no_log(self) -> None:
        payload = {"hookEventName": "SessionStart"}
        self._run_main(False, payload)
        log_path = self.tmppath / "lifecycle_payload_logger.debug.log"
        self.assertFalse(log_path.exists())

    def test_LC002_debug_enabled_target_event_writes_log(self) -> None:
        payload = {"hookEventName": "SessionStart"}
        self._run_main(True, payload)
        content = self._log_content()
        self.assertIn("input_json", content)

    def test_LC003_debug_enabled_non_target_event_skipped(self) -> None:
        payload = {"hookEventName": "PreToolUse", "tool_name": "read_file", "tool_input": {}}
        self._run_main(True, payload)
        content = self._log_content()
        self.assertIn("skip", content)
        self.assertNotIn("input_json", content)

    def test_LC004_log_line_has_timestamp_prefix(self) -> None:
        import re
        payload = {"hookEventName": "SubagentStart"}
        self._run_main(True, payload)
        content = self._log_content()
        timestamp_pattern = re.compile(r"\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}")
        self.assertTrue(any(timestamp_pattern.match(line) for line in content.splitlines()))

    def test_LC005_all_target_events_logged(self) -> None:
        target_events = ("SessionStart", "Stop", "SubagentStart", "SubagentStop")
        for event_name in target_events:
            with self.subTest(event=event_name):
                self._tmpdir.cleanup()
                self._tmpdir = tempfile.TemporaryDirectory()
                self.tmppath = Path(self._tmpdir.name)
                self._run_main(True, {"hookEventName": event_name})
                self.assertIn("input_json", self._log_content())

    def test_LC006_payload_not_double_serialized(self) -> None:
        payload = {"hookEventName": "SessionStart", "key": "value"}
        self._run_main(True, payload)
        content = self._log_content()
        # Double-serialized payload would appear as an escaped JSON string with \\".
        # Proper structured output contains the key/value directly without extra escaping.
        self.assertNotIn('\\"key\\"', content)
        self.assertIn("key", content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
