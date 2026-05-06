#!/usr/bin/env python3
"""Unit tests for debug_logging.py"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(r"c:\GHC\.github\hooks\scripts")
sys.path.insert(0, str(SCRIPTS_DIR))

from debug_logging import (
    build_debug_paths,
    is_debug_enabled,
    append_debug_line,
    HookDebugLogger,
)


class TestBuildDebugPaths(unittest.TestCase):

    def test_DL001_flag_path_name(self):
        script_dir = Path("/some/dir")
        flag, _ = build_debug_paths(script_dir, "foo")
        self.assertEqual(flag.name, "foo.debug")

    def test_DL002_log_path_name(self):
        script_dir = Path("/some/dir")
        _, log = build_debug_paths(script_dir, "foo")
        self.assertEqual(log.name, "foo.debug.log")


class TestIsDebugEnabled(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmppath = Path(self._tmpdir.name)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_DL003_flag_file_exists(self):
        flag = self.tmppath / "test.debug"
        flag.touch()
        self.assertTrue(is_debug_enabled(flag))

    def test_DL004_flag_file_absent(self):
        flag = self.tmppath / "test.debug"
        self.assertFalse(is_debug_enabled(flag))


class TestHookDebugLogger(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmppath = Path(self._tmpdir.name)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_DL005_log_with_kwargs_when_enabled(self):
        flag = self.tmppath / "test.debug"
        flag.touch()
        logger = HookDebugLogger(self.tmppath, "test")
        logger.log("input", key="value")
        log_file = self.tmppath / "test.debug.log"
        content = log_file.read_text(encoding="utf-8")
        self.assertIn("input", content)
        self.assertIn("key", content)

    def test_DL006_log_without_kwargs_when_enabled(self):
        flag = self.tmppath / "test.debug"
        flag.touch()
        logger = HookDebugLogger(self.tmppath, "test")
        logger.log("done")
        log_file = self.tmppath / "test.debug.log"
        content = log_file.read_text(encoding="utf-8")
        # kwargs なしの場合はメッセージのみ
        self.assertIn("done", content)
        self.assertTrue(content.strip().endswith("done"))

    def test_DL007_log_does_nothing_when_disabled(self):
        logger = HookDebugLogger(self.tmppath, "test")
        logger.log("skip", reason="test")
        log_file = self.tmppath / "test.debug.log"
        self.assertFalse(log_file.exists())


class TestAppendDebugLine(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmppath = Path(self._tmpdir.name)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_DL008_creates_new_file(self):
        log = self.tmppath / "new.debug.log"
        self.assertFalse(log.exists())
        append_debug_line(log, "first line")
        self.assertTrue(log.exists())
        self.assertIn("first line", log.read_text(encoding="utf-8"))

    def test_DL009_appends_to_existing_file(self):
        log = self.tmppath / "existing.debug.log"
        log.write_text("line1\n", encoding="utf-8")
        append_debug_line(log, "line2")
        content = log.read_text(encoding="utf-8")
        self.assertIn("line1", content)
        self.assertIn("line2", content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
