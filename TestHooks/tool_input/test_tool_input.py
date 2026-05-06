#!/usr/bin/env python3
"""Unit tests for tool_input.py"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(r"c:\GHC\.github\hooks\scripts")
sys.path.insert(0, str(SCRIPTS_DIR))

from tool_input import is_write_tool, is_read_tool, get_written_paths, get_read_paths, get_command


class TestIsWriteTool(unittest.TestCase):

    def test_TI001_create_file(self):
        self.assertTrue(is_write_tool("create_file"))

    def test_TI002_replace_string_in_file(self):
        self.assertTrue(is_write_tool("replace_string_in_file"))

    def test_TI003_multi_replace_string_in_file(self):
        self.assertTrue(is_write_tool("multi_replace_string_in_file"))

    def test_TI004_non_write_tool(self):
        self.assertFalse(is_write_tool("read_file"))


class TestIsReadTool(unittest.TestCase):

    def test_TI005_read_file(self):
        self.assertTrue(is_read_tool("read_file"))

    def test_TI006_list_dir(self):
        self.assertTrue(is_read_tool("list_dir"))

    def test_TI007_view_image(self):
        self.assertTrue(is_read_tool("view_image"))

    def test_TI008_non_read_tool(self):
        self.assertFalse(is_read_tool("create_file"))


class TestGetWrittenPaths(unittest.TestCase):

    def test_TI009_create_file_with_filepath(self):
        self.assertEqual(get_written_paths("create_file", {"filePath": "a.py"}), ["a.py"])

    def test_TI010_create_file_no_filepath(self):
        self.assertEqual(get_written_paths("create_file", {}), [])

    def test_TI011_multi_replace_array(self):
        tool_input = {
            "replacements": [
                {"filePath": "docs/a.md", "oldString": "x", "newString": "y"},
                {"filePath": "docs/b.md", "oldString": "x", "newString": "y"},
            ]
        }
        result = get_written_paths("multi_replace_string_in_file", tool_input)
        self.assertEqual(result, ["docs/a.md", "docs/b.md"])

    def test_TI012_multi_replace_empty_replacements_fallback(self):
        tool_input = {"replacements": [], "filePath": "docs/x.md"}
        result = get_written_paths("multi_replace_string_in_file", tool_input)
        self.assertEqual(result, ["docs/x.md"])

    def test_TI013_non_write_tool_returns_empty(self):
        self.assertEqual(get_written_paths("read_file", {"filePath": "x.py"}), [])


class TestGetReadPaths(unittest.TestCase):

    def test_TI014_read_file(self):
        self.assertEqual(get_read_paths("read_file", {"filePath": "x.py"}), ["x.py"])

    def test_TI015_list_dir(self):
        self.assertEqual(get_read_paths("list_dir", {"path": "/tmp"}), ["/tmp"])

    def test_TI017_non_read_tool_returns_empty(self):
        self.assertEqual(get_read_paths("create_file", {"filePath": "x.py"}), [])

    def test_TI018_view_image(self):
        self.assertEqual(get_read_paths("view_image", {"filePath": "img.png"}), ["img.png"])

    def test_TI019_read_file_no_filepath(self):
        self.assertEqual(get_read_paths("read_file", {}), [])

    def test_TI020_list_dir_no_path(self):
        self.assertEqual(get_read_paths("list_dir", {}), [])


class TestGetCommand(unittest.TestCase):

    def test_TI016_get_command(self):
        self.assertEqual(get_command({"command": "ls -la"}), "ls -la")

    def test_TI021_get_command_no_key(self):
        self.assertEqual(get_command({}), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
