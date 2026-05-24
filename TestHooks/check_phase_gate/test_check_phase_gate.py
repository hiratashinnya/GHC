#!/usr/bin/env python3
"""Unit tests for check_phase_gate.py"""

from __future__ import annotations

import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

LOCAL_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / ".github" / "hooks" / "scripts"
SCRIPTS_DIR = LOCAL_SCRIPTS_DIR if LOCAL_SCRIPTS_DIR.is_dir() else Path(r"c:\GHC\.github\hooks\scripts")
for relative in ("core", "access_control", "tooling", "shared", "entrypoints"):
    sys.path.insert(0, str(SCRIPTS_DIR / relative))

from check_phase_gate import (
    _scalar,
    _extract_variant,
    parse_frontmatter,
    infer_process,
    parse_write_target,
    check_gate_compliance,
    WorkflowIdentifier,
    WorkflowDocument,
    GateCheckResult,
    PROCESS_NAMES,
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


class TestExtractVariant(unittest.TestCase):

    def test_CG014_no_variant(self):
        self.assertIsNone(_extract_variant("03-decisions.md", 3))

    def test_CG015_overview_variant(self):
        self.assertEqual(_extract_variant("03-decisions-overview.md", 3), "overview")

    def test_CG016_comp_id_variant(self):
        self.assertEqual(_extract_variant("03-decisions-auth.md", 3), "auth")

    def test_CG017_artifact_subtype_stripped(self):
        # "04-artifact-auth-api.md" → variant は "auth"（api を除去）
        self.assertEqual(_extract_variant("04-artifact-auth-api.md", 4), "auth")

    def test_CG018_artifact_no_subtype(self):
        self.assertEqual(_extract_variant("04-artifact-auth.md", 4), "auth")


class TestParseWriteTarget(unittest.TestCase):

    def test_CG019_docs_simple(self):
        doc = parse_write_target("docs/basic-design/01-validation.md")
        self.assertIsNotNone(doc)
        self.assertEqual(doc.scope, "docs")
        self.assertEqual(doc.idx.phase, "basic-design")
        self.assertEqual(doc.idx.process, 1)
        self.assertIsNone(doc.idx.variant)

    def test_CG020_docs_overview(self):
        doc = parse_write_target("docs/detailed-design/03-decisions-overview.md")
        self.assertIsNotNone(doc)
        self.assertEqual(doc.idx.phase, "detailed-design")
        self.assertEqual(doc.idx.process, 3)
        self.assertEqual(doc.idx.variant, "overview")

    def test_CG021_docs_components(self):
        doc = parse_write_target("docs/detailed-design/components/auth/04-artifact-auth.md")
        self.assertIsNotNone(doc)
        self.assertEqual(doc.scope, "docs")
        self.assertEqual(doc.idx.phase, "detailed-design")
        self.assertEqual(doc.idx.process, 4)
        self.assertEqual(doc.idx.variant, "auth")

    def test_CG022_iter_path(self):
        doc = parse_write_target("iter/iter2/phase3/04-artifact.md")
        self.assertIsNotNone(doc)
        self.assertEqual(doc.scope, "iter")
        self.assertEqual(doc.idx.phase, "detailed-design")
        self.assertEqual(doc.idx.process, 4)
        self.assertEqual(doc.idx.iteration, 2)

    def test_CG023_windows_backslash(self):
        a = parse_write_target("docs/basic-design/01-validation.md")
        b = parse_write_target("docs\\basic-design\\01-validation.md")
        self.assertEqual(a, b)

    def test_CG024_invalid_path(self):
        self.assertIsNone(parse_write_target("src/foo.py"))


class TestPrecedingGates(unittest.TestCase):

    def _make_idx(self, phase, phase_index, process, iteration=0, variant=None):
        from check_phase_gate import PHASES
        return WorkflowIdentifier(phase=phase, process=process, iteration=iteration, variant=variant)

    def test_CG025_process1_phase_gt1(self):
        idx = self._make_idx("basic-design", 2, 1)
        gates = idx.preceding_gates()
        self.assertIn(
            WorkflowIdentifier("requirements", 5, 0, None),
            gates,
        )

    def test_CG026_process4_no_variant(self):
        idx = self._make_idx("basic-design", 2, 4)
        gates = idx.preceding_gates()
        self.assertIn(WorkflowIdentifier("basic-design", 3, 0, None), gates)
        # overview が追加されないこと
        self.assertNotIn(WorkflowIdentifier("basic-design", 3, 0, "overview"), gates)

    def test_CG027_process4_comp_id(self):
        idx = WorkflowIdentifier("detailed-design", 4, 0, "auth")
        gates = idx.preceding_gates()
        # variant 版と overview 版の両方が必要
        self.assertIn(WorkflowIdentifier("detailed-design", 3, 0, "auth"), gates)
        self.assertIn(WorkflowIdentifier("detailed-design", 3, 0, "overview"), gates)

    def test_CG028_no_gates(self):
        idx = WorkflowIdentifier("requirements", 1, 2, None)  # process=1, phase index=1
        self.assertEqual(idx.preceding_gates(), [])


class TestExpectedPath(unittest.TestCase):

    def test_CG029_docs_simple(self):
        doc = WorkflowDocument(
            scope="docs",
            idx=WorkflowIdentifier("basic-design", 3, 0, None),
            path=None,
        )
        self.assertEqual(doc._expected_path(), "docs/basic-design/03-decisions.md")

    def test_CG030_docs_overview(self):
        doc = WorkflowDocument(
            scope="docs",
            idx=WorkflowIdentifier("detailed-design", 3, 0, "overview"),
            path=None,
        )
        self.assertEqual(doc._expected_path(), "docs/detailed-design/03-decisions-overview.md")

    def test_CG031_docs_comp_id(self):
        doc = WorkflowDocument(
            scope="docs",
            idx=WorkflowIdentifier("detailed-design", 3, 0, "auth"),
            path=None,
        )
        self.assertEqual(
            doc._expected_path(),
            "docs/detailed-design/components/auth/03-decisions-auth.md",
        )

    def test_CG032_iter(self):
        doc = WorkflowDocument(
            scope="iter",
            idx=WorkflowIdentifier("detailed-design", 5, 2, None),
            path=None,
        )
        self.assertEqual(doc._expected_path(), "iter/iter2/phase3/05-verification.md")


class TestCheckGateCompliance(unittest.TestCase):
    """check_gate_compliance() の統合テスト。tmpdir に実ファイルを作成して検証する。"""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._orig_cwd = os.getcwd()
        os.chdir(self._tmpdir.name)

    def tearDown(self):
        os.chdir(self._orig_cwd)
        self._tmpdir.cleanup()

    def _write_md(self, rel_path: str, status: str = "approved"):
        p = Path(rel_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(f"""\
            ---
            approval-required: true
            status: {status}
            ---
        """), encoding="utf-8")

    def test_CG033_no_gates_required(self):
        # requirements phase process=2 → 直前ゲートなし
        target = parse_write_target("docs/requirements/02-breakdown.md")
        result = check_gate_compliance(target)
        self.assertFalse(result.blocked)

    def test_CG034_missing_gate(self):
        # basic-design process=1 → requirements/05-verification.md が必要
        target = parse_write_target("docs/basic-design/01-validation.md")
        result = check_gate_compliance(target)
        self.assertTrue(result.blocked)
        self.assertEqual(len(result.missing), 1)
        self.assertEqual(result.missing[0].idx.phase, "requirements")
        self.assertEqual(result.missing[0].idx.process, 5)

    def test_CG035_approved_gate(self):
        self._write_md("docs/requirements/05-verification.md", "approved")
        target = parse_write_target("docs/basic-design/01-validation.md")
        result = check_gate_compliance(target)
        self.assertFalse(result.blocked)

    def test_CG036_unapproved_gate(self):
        self._write_md("docs/requirements/05-verification.md", "draft")
        target = parse_write_target("docs/basic-design/01-validation.md")
        result = check_gate_compliance(target)
        self.assertTrue(result.blocked)
        self.assertEqual(len(result.violations), 1)
        self.assertEqual(result.violations[0].idx.process, 5)

    def test_CG037_naming_violation(self):
        # 期待パスとは別名でゲートファイルが存在する
        self._write_md("docs/requirements/05-verification-extra.md", "approved")
        target = parse_write_target("docs/basic-design/01-validation.md")
        result = check_gate_compliance(target)
        self.assertTrue(result.blocked)
        self.assertEqual(len(result.naming_violations), 1)

    def test_CG038_comp_id_both_gates_approved(self):
        # detailed-design の comp=auth, process=4 → decisions-auth + decisions-overview が必要
        self._write_md("docs/detailed-design/components/auth/03-decisions-auth.md", "approved")
        self._write_md("docs/detailed-design/03-decisions-overview.md", "approved")
        target = WorkflowDocument(
            scope="docs",
            idx=WorkflowIdentifier("detailed-design", 4, 0, "auth"),
            path="docs/detailed-design/components/auth/04-artifact-auth.md",
        )
        result = check_gate_compliance(target)
        self.assertFalse(result.blocked)

    def test_CG039_comp_id_overview_missing(self):
        self._write_md("docs/detailed-design/components/auth/03-decisions-auth.md", "approved")
        # overview は意図的に作らない
        target = WorkflowDocument(
            scope="docs",
            idx=WorkflowIdentifier("detailed-design", 4, 0, "auth"),
            path="docs/detailed-design/components/auth/04-artifact-auth.md",
        )
        result = check_gate_compliance(target)
        self.assertTrue(result.blocked)
        missing_variants = [m.idx.variant for m in result.missing]
        self.assertIn("overview", missing_variants)


if __name__ == "__main__":
    unittest.main(verbosity=2)
