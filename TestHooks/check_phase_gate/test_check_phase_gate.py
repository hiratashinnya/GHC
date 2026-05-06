#!/usr/bin/env python3
"""Unit tests for check_phase_gate.py"""

from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(r"c:\GHC\.github\hooks\scripts")
sys.path.insert(0, str(SCRIPTS_DIR))

from check_phase_gate import (
    _scalar,
    parse_frontmatter,
    infer_process,
    parse_target,
    required_gate_specs,
    evaluate,
    collect_gate_docs,
)


class TestScalar(unittest.TestCase):

    def test_CG001_plain_string(self):
        self.assertEqual(_scalar("hello"), "hello")

    def test_CG002_bool_true(self):
        self.assertIs(_scalar("true"), True)

    def test_CG003_bool_false(self):
        self.assertIs(_scalar("false"), False)

    def test_CG004_null(self):
        self.assertIsNone(_scalar("null"))

    def test_CG005_integer(self):
        self.assertEqual(_scalar("5"), 5)

    def test_CG006_double_quoted_string(self):
        self.assertEqual(_scalar('"foo"'), "foo")

    def test_CG007_empty_string(self):
        self.assertIsNone(_scalar(""))


class TestParseFrontmatter(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmppath = Path(self._tmpdir.name)

    def tearDown(self):
        self._tmpdir.cleanup()

    def _write_md(self, name: str, content: str) -> Path:
        p = self.tmppath / name
        p.write_text(textwrap.dedent(content), encoding="utf-8")
        return p

    def test_CG008_valid_frontmatter(self):
        md = self._write_md("ok.md", """\
            ---
            approval-required: true
            status: approved
            phase: basic-design
            process: 3
            ---
            Body text.
        """)
        result = parse_frontmatter(md)
        self.assertIsNotNone(result)
        self.assertIs(result["approval-required"], True)
        self.assertEqual(result["status"], "approved")
        self.assertEqual(result["phase"], "basic-design")
        self.assertEqual(result["process"], 3)

    def test_CG009_no_frontmatter(self):
        md = self._write_md("no_fm.md", "Just some text.\n")
        self.assertIsNone(parse_frontmatter(md))

    def test_CG010_nonexistent_path(self):
        self.assertIsNone(parse_frontmatter(self.tmppath / "missing.md"))


class TestInferProcess(unittest.TestCase):

    def test_CG011_process_01(self):
        self.assertEqual(infer_process("01-validation.md"), 1)

    def test_CG012_process_05_compound_name(self):
        self.assertEqual(infer_process("05-verification-comp.md"), 5)

    def test_CG013_no_match(self):
        self.assertIsNone(infer_process("README.md"))


class TestParseTarget(unittest.TestCase):

    def test_CG014_docs_posix_path(self):
        result = parse_target("docs/basic-design/01-validation.md")
        self.assertIsNotNone(result)
        self.assertEqual(result["scope"], "docs")
        self.assertEqual(result["phase"], "basic-design")
        self.assertEqual(result["process"], 1)

    def test_CG015_iter_path(self):
        result = parse_target("iter/iter2/phase3/04-artifact.md")
        self.assertIsNotNone(result)
        self.assertEqual(result["scope"], "iter")
        self.assertEqual(result["phase"], "detailed-design")
        self.assertEqual(result["process"], 4)
        self.assertEqual(result["iteration"], 2)

    def test_CG016_windows_backslash(self):
        a = parse_target("docs/basic-design/01-validation.md")
        b = parse_target("docs\\basic-design\\01-validation.md")
        self.assertEqual(a, b)

    def test_CG017_invalid_path(self):
        self.assertIsNone(parse_target("src/foo.py"))


class TestRequiredGateSpecs(unittest.TestCase):

    def _make_target(self, phase, phase_index, process, scope="docs", iteration=0):
        return {
            "scope": scope,
            "phase": phase,
            "phase_index": phase_index,
            "process": process,
            "iteration": iteration,
            "target_path": f"docs/{phase}/0{process}-x.md",
        }

    def test_CG018_process1_phase_index_gt1(self):
        target = self._make_target("basic-design", 2, 1)
        specs = required_gate_specs(target)
        # 前フェーズ (requirements) の process 5 が必要
        self.assertIn(("requirements", 5, 0), specs)

    def test_CG019_process_ge4(self):
        target = self._make_target("basic-design", 2, 4)
        specs = required_gate_specs(target)
        # 同フェーズ process 3 が必要
        self.assertIn(("basic-design", 3, 0), specs)

    def test_CG020_no_requirements(self):
        target = self._make_target("requirements", 1, 2)
        specs = required_gate_specs(target)
        self.assertEqual(specs, [])


class TestEvaluate(unittest.TestCase):

    def _make_target(self, phase="basic-design", phase_index=2, process=1, iteration=0):
        return {
            "scope": "docs",
            "phase": phase,
            "phase_index": phase_index,
            "process": process,
            "iteration": iteration,
            "target_path": f"docs/{phase}/0{process}-x.md",
        }

    def test_CG021_missing_requirement(self):
        target = self._make_target()  # phase_index=2, process=1 → 前フェーズproc5必須
        result = evaluate(target, [])
        self.assertTrue(result["blocked"])
        self.assertEqual(result["violations"], [])
        self.assertEqual(result["missing_requirements"],  [{'phase': 'requirements', 'process': 5, 'iteration': 0}])
        self.assertGreaterEqual(len(result["requirements"]), 1)  # 要件ドキュメントの情報も返す

    def test_CG022_violation_unapproved(self):
        target = self._make_target()
        gate_docs = [{
            "path": "docs/requirements/05-verification.md",
            "phase": "requirements",
            "process": 5,
            "iteration": 0,
            "status": "draft",  # 未承認
        }]
        result = evaluate(target, gate_docs)
        self.assertTrue(result["blocked"])
        self.assertEqual(result["violations"], gate_docs)  # 要件ドキュメントが違反として返る
        self.assertEqual(result["missing_requirements"], [])
        self.assertGreaterEqual(len(result["requirements"]), 1)  # 要件ドキュメントの情報も返す

    def test_CG023_approved(self):
        target = self._make_target()
        gate_docs = [{
            "path": "docs/requirements/05-verification.md",
            "phase": "requirements",
            "process": 5,
            "iteration": 0,
            "status": "approved",
        }]
        result = evaluate(target, gate_docs)
        self.assertFalse(result["blocked"])
        self.assertEqual(result["violations"], [])
        self.assertEqual(result["missing_requirements"], [])
        self.assertGreaterEqual(len(result["requirements"]), 1)  # 要件ドキュメントの情報も返す


class TestCollectGateDocs(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmppath = Path(self._tmpdir.name)
        self.docs_dir = self.tmppath / "docs"
        self.iter_dir = self.tmppath / "iter"
        self.docs_dir.mkdir()
        self.iter_dir.mkdir()

    def tearDown(self):
        self._tmpdir.cleanup()

    def _write_md(self, rel_path: str, content: str):
        p = self.tmppath / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(content), encoding="utf-8")
        return p

    def test_CG024_excludes_dashboard(self):
        self._write_md("docs/dashboard.md", """\
            ---
            approval-required: true
            status: approved
            phase: requirements
            process: 5
            ---
        """)
        result = collect_gate_docs(self.docs_dir, self.iter_dir)
        paths = [r["path"] for r in result]
        self.assertFalse(any("dashboard.md" in p for p in paths))

    def test_CG025_approval_required_filter(self):
        self._write_md("docs/requirements/05-verification.md", """\
            ---
            approval-required: true
            status: approved
            phase: requirements
            process: 5
            ---
        """)
        self._write_md("docs/requirements/03-decisions.md", """\
            ---
            approval-required: false
            status: approved
            phase: requirements
            process: 3
            ---
        """)
        result = collect_gate_docs(self.docs_dir, self.iter_dir)
        self.assertEqual(len(result), 1)
        self.assertIn("05-verification.md", result[0]["path"])

    def test_CG026_empty_directory(self):
        result = collect_gate_docs(self.docs_dir, self.iter_dir)
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
