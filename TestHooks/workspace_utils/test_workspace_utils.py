#!/usr/bin/env python3
"""Unit tests for workspace_utils.py"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

LOCAL_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / ".github" / "hooks" / "scripts"
SCRIPTS_DIR = LOCAL_SCRIPTS_DIR if LOCAL_SCRIPTS_DIR.is_dir() else Path(r"c:\GHC\.github\hooks\scripts")
for relative in ("core", "access_control", "tooling", "shared", "entrypoints"):
    sys.path.insert(0, str(SCRIPTS_DIR / relative))

from workspace_utils import to_workspace_relative, is_under_dir, dedup_paths
from _lib._io import norm


class TestNorm(unittest.TestCase):

    def test_WU001_backslash_conversion(self):
        self.assertEqual(norm("docs\\basic-design\\x.md"), "docs/basic-design/x.md")

    def test_WU002_already_posix(self):
        self.assertEqual(norm("docs/basic-design/x.md"), "docs/basic-design/x.md")

    def test_WU003_empty_string(self):
        self.assertEqual(norm(""), "")


class TestToWorkspaceRelative(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tmpdir.name).resolve()

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_WU004_absolute_path_inside(self):
        target = self.workspace / "docs" / "x.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()
        result = to_workspace_relative(str(target), self.workspace)
        self.assertEqual(result, "docs/x.md")

    def test_WU005_relative_path_inside(self):
        (self.workspace / "docs").mkdir(parents=True, exist_ok=True)
        result = to_workspace_relative("docs/x.md", self.workspace)
        self.assertEqual(result, "docs/x.md")

    def test_WU006_outside_workspace(self):
        # tmpdir の親ディレクトリに存在するファイルは workspace 外
        outside = self.workspace.parent / "outside_test_file.md"
        result = to_workspace_relative(str(outside), self.workspace)
        self.assertIsNone(result)

    def test_WU007_workspace_root_file(self):
        target = self.workspace / "README.md"
        target.touch()
        result = to_workspace_relative(str(target), self.workspace)
        self.assertEqual(result, "README.md")


class TestIsUnderDir(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tmpdir.name).resolve()

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_WU008_file_under_docs(self):
        docs = self.workspace / "docs"
        docs.mkdir(parents=True, exist_ok=True)
        (docs / "x.md").touch()
        self.assertTrue(is_under_dir("docs/x.md", "docs", self.workspace))

    def test_WU009_exact_dir_match(self):
        (self.workspace / "docs").mkdir(parents=True, exist_ok=True)
        self.assertTrue(is_under_dir("docs", "docs", self.workspace))

    def test_WU010_sibling_directory(self):
        self.assertFalse(is_under_dir("iter/x.md", "docs", self.workspace))

    def test_WU011_outside_workspace(self):
        outside = str(self.workspace.parent / "outside.md")
        self.assertFalse(is_under_dir(outside, "docs", self.workspace))


class TestDedupPaths(unittest.TestCase):

    def test_WU012_no_duplicates(self):
        self.assertEqual(dedup_paths(["a.md", "b.md"]), ["a.md", "b.md"])

    def test_WU013_exact_duplicates(self):
        self.assertEqual(dedup_paths(["a.md", "a.md"]), ["a.md"])

    def test_WU014_slash_mismatch_duplicates(self):
        result = dedup_paths(["docs\\x.md", "docs/x.md"])
        self.assertEqual(result, ["docs/x.md"])

    def test_WU015_empty_list(self):
        self.assertEqual(dedup_paths([]), [])

    def test_WU016_preserves_insertion_order(self):
        self.assertEqual(dedup_paths(["b.md", "a.md", "b.md"]), ["b.md", "a.md"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
