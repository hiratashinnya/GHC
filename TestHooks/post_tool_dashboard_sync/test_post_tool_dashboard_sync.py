#!/usr/bin/env python3
"""Unit tests for post_tool_dashboard_sync.py"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

LOCAL_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / ".github" / "hooks" / "scripts"
SCRIPTS_DIR = LOCAL_SCRIPTS_DIR if LOCAL_SCRIPTS_DIR.is_dir() else Path(r"c:\GHC\.github\hooks\scripts")
for relative in ("core", "access_control", "tooling", "shared", "entrypoints"):
    sys.path.insert(0, str(SCRIPTS_DIR / relative))

from hook_payload import PostToolUsePayload
from post_tool_dashboard_sync import _should_skip, _build_patch_cmd


class TestShouldSkip(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tmpdir.name).resolve()

    def tearDown(self):
        self._tmpdir.cleanup()

    def _make_event(self, tool_name: str, tool_input: dict) -> PostToolUsePayload:
        return PostToolUsePayload.from_dict({
            "hookEventName": "PostToolUse",
            "tool_name": tool_name,
            "tool_input": tool_input,
            "cwd": str(self.workspace),
        })

    def test_DS001_non_write_tool(self):
        event = self._make_event("read_file", {"filePath": "docs/x.md"})
        reason, changed_file = _should_skip(event, self.workspace)
        self.assertEqual(reason, "non-write tool")
        self.assertIsNone(changed_file)

    def test_DS002_non_docs_file(self):
        event = self._make_event("create_file", {"filePath": "src/foo.py"})
        reason, changed_file = _should_skip(event, self.workspace)
        self.assertEqual(reason, "not a docs/ .md file")
        self.assertEqual(changed_file, "src/foo.py")  # changed_file は返す（後続処理で docs かどうか再確認するため）

    def test_DS003_docs_relative_md(self):
        event = self._make_event("create_file", {"filePath": "docs/x.md"})
        reason, changed_file = _should_skip(event, self.workspace)
        self.assertIsNone(reason)
        self.assertEqual(changed_file, "docs/x.md")

    def test_DS004_docs_absolute_md(self):
        abs_path = str(self.workspace / "docs" / "x.md")
        event = self._make_event("create_file", {"filePath": abs_path})
        reason, changed_file = _should_skip(event, self.workspace)
        self.assertIsNone(reason)
        self.assertEqual(changed_file, "docs/x.md")

    def test_DS005_docs_non_md_extension(self):
        event = self._make_event("create_file", {"filePath": "docs/x.txt"})
        reason, changed_file = _should_skip(event, self.workspace)
        self.assertEqual(reason, "not a docs/ .md file")
        self.assertEqual(changed_file, "docs/x.txt")  # changed_file は返す（後続処理で docs かどうか再確認するため）

    def test_DS011_multi_replace_docs_md(self):
        abs_path = str(self.workspace / "docs" / "y.md")
        event = self._make_event(
            "multi_replace_string_in_file",
            {"replacements": [{"filePath": abs_path, "oldString": "a", "newString": "b"}]},
        )
        reason, changed_file = _should_skip(event, self.workspace)
        self.assertIsNone(reason)
        self.assertEqual(changed_file, "docs/y.md")


class TestBuildPatchCmd(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.patch_script = Path(self._tmpdir.name) / "patch_dashboard.py"
        self.patch_script.touch()

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_DS006_with_changed_file(self):
        cmd = _build_patch_cmd(self.patch_script, "docs/x.md")
        self.assertIn("--changed-file", cmd)
        idx = cmd.index("--changed-file")
        self.assertEqual(cmd[idx + 1], "docs/x.md")

    def test_DS007_without_changed_file(self):
        cmd = _build_patch_cmd(self.patch_script, None)
        self.assertNotIn("--changed-file", cmd)


class TestMain(unittest.TestCase):
    """Integration tests: run main() via stdin mock and subprocess mock."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tmpdir.name).resolve()
        # patch_script が存在しないと preconditions で warn になる → 必要な場合は作成
        scripts_path = self.workspace / ".github" / "scripts"
        scripts_path.mkdir(parents=True)
        self.patch_script = scripts_path / "patch_dashboard.py"
        self.patch_script.touch()

    def tearDown(self):
        self._tmpdir.cleanup()

    def _make_stdin_mock(self, payload: dict):
        mock = MagicMock()
        mock.isatty.return_value = False
        mock.buffer.read.return_value = json.dumps(payload).encode("utf-8")
        return mock

    def _run_main(self, payload: dict):
        """Run main() with the given payload; return stdout text."""
        buf = io.StringIO()
        with patch("hook_payload.sys.stdin", self._make_stdin_mock(payload)), \
             patch("sys.stdout", buf):
            try:
                from post_tool_dashboard_sync import main
                main()
            except SystemExit:
                pass
        return buf.getvalue()

    def test_DS008_non_write_tool_skips(self):
        payload = {
            "hookEventName": "PostToolUse",
            "tool_name": "read_file",
            "tool_input": {},
            "cwd": str(self.workspace),
        }
        with patch("subprocess.run") as mock_run:
            self._run_main(payload)
            mock_run.assert_not_called()

    def test_DS009_non_docs_file_skips(self):
        payload = {
            "hookEventName": "PostToolUse",
            "tool_name": "create_file",
            "tool_input": {"filePath": "src/foo.py", "content": ""},
            "cwd": str(self.workspace),
        }
        with patch("subprocess.run") as mock_run:
            self._run_main(payload)
            mock_run.assert_not_called()

    def test_DS010_docs_md_calls_patch(self):
        payload = {
            "hookEventName": "PostToolUse",
            "tool_name": "create_file",
            "tool_input": {"filePath": "docs/x.md", "content": ""},
            "cwd": str(self.workspace),
        }
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            self._run_main(payload)
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]  # 第1引数のコマンドリスト
            self.assertIn("--changed-file", call_args)
            idx = call_args.index("--changed-file")
            self.assertEqual(call_args[idx + 1], "docs/x.md")


if __name__ == "__main__":
    unittest.main(verbosity=2)
