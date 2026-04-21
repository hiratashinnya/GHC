#!/usr/bin/env python3
"""I-2: verify-iteration-assignment — Verify all REQs assigned across iterations.

Usage:
  python verify_iteration_assignment.py
         [--iterations-dir docs/requirements/iterations]
         [--breakdown docs/requirements/02-breakdown.md]

Checks:
  - All REQ-F IDs from breakdown are assigned to exactly one iteration
  - No duplicate assignments
  - input-refs in iteration files resolve correctly

Output: JSON  { success, total_reqs, assigned_reqs, unassigned, issues }
"""
import sys, os, re, argparse
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib

_S = "I-2:verify-iteration-assignment"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iterations-dir", default="docs/requirements/iterations",
                    help="Directory containing iteration artifact files")
    ap.add_argument("--breakdown", default="docs/requirements/02-breakdown.md",
                    help="Breakdown document with all REQ-F definitions")
    args = ap.parse_args()

    _lib.debug_log(_S, "start", idir=args.iterations_dir, bd=args.breakdown)

    bd_text = _lib.read_text(args.breakdown) or ""
    all_reqs = set(re.findall(r"REQ-F-\d+", bd_text))

    idir = Path(args.iterations_dir)
    assigned = {}
    duplicates = []
    issues = []

    if idir.exists():
        for fp in sorted(idir.glob("*.md")):
            text = _lib.read_text(str(fp)) or ""
            reqs = set(re.findall(r"REQ-F-\d+", text))
            for r in reqs:
                if r in assigned:
                    duplicates.append({
                        "req": r,
                        "files": [assigned[r], _lib.norm(fp)],
                    })
                else:
                    assigned[r] = _lib.norm(fp)

    unassigned = sorted(all_reqs - set(assigned.keys()))
    if unassigned:
        issues.append({"issue": "unassigned_reqs", "reqs": unassigned})
    if duplicates:
        issues.append({"issue": "duplicate_assignments", "duplicates": duplicates})

    if idir.exists():
        for fp in sorted(idir.glob("*.md")):
            fm = _lib.parse_fm(str(fp))
            if not fm:
                continue
            for ref in (fm.get("input-refs") or []):
                if not isinstance(ref, dict):
                    continue
                rp = ref.get("path", "")
                resolved = os.path.normpath(os.path.join(str(fp.parent), rp))
                if not os.path.exists(resolved):
                    issues.append({
                        "issue": "input_ref_missing",
                        "file": _lib.norm(fp),
                        "ref": rp,
                    })

    ok = len(issues) == 0
    _lib.debug_log(_S, "done", ok=ok, total=len(all_reqs), assigned=len(assigned))
    _lib.out_json({
        "success": ok,
        "total_reqs": len(all_reqs),
        "assigned_reqs": len(assigned),
        "unassigned": unassigned,
        "issues": issues,
    })


if __name__ == "__main__":
    main()
