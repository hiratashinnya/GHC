#!/usr/bin/env python3
"""M-1: check-merge-prerequisites — Verify diff doc is ready for merge.

Usage:
  python check_merge_prerequisites.py <diff_file>

Output: JSON  { success, file, issues }
"""
import sys, os, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib

_S = "M-1:check-merge-prerequisites"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("diff_file", help="Path to the diff document in iter/")
    args = ap.parse_args()

    _lib.debug_log(_S, "start", diff=args.diff_file)

    fm = _lib.parse_fm(args.diff_file)
    if not fm:
        _lib.out_err(f"Cannot parse frontmatter: {args.diff_file}")

    issues = []

    if fm.get("status") != "approved":
        issues.append(f"status is '{fm.get('status')}', expected 'approved'")
    if fm.get("doc-kind") != "diff":
        issues.append(f"doc-kind is '{fm.get('doc-kind')}', expected 'diff'")
    if fm.get("base-version") is None:
        issues.append("base-version is missing")
    if fm.get("approval-required"):
        if not fm.get("approved-by"):
            issues.append("approval-required but approved-by is empty")
        if not fm.get("approved-at"):
            issues.append("approval-required but approved-at is empty")

    ok = len(issues) == 0
    _lib.debug_log(_S, "done", ok=ok, issues=issues)
    _lib.out_json({
        "success": ok,
        "file": _lib.norm(args.diff_file),
        "issues": issues,
    })


if __name__ == "__main__":
    main()
