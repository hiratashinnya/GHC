#!/usr/bin/env python3
"""M-3: bump-version — Increment master version after merge.

Usage:
  python bump_version.py <master_file> [--cross-iteration]

Rules:
  process ①②④  → minor increment (1.0 → 1.1), status reset to draft
  process ③⑤   → minor increment, keep status if already approved
  --cross-iteration → major increment (1.x → 2.0)

Output: JSON  { success, file, old_version, new_version, updates }
"""
import sys, os, argparse
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib

_S = "M-3:bump-version"


def _bump(version_str, major=False):
    parts = str(version_str).split(".")
    if len(parts) < 2:
        parts = [parts[0], "0"]
    if major:
        return f"{int(parts[0]) + 1}.0"
    return f"{parts[0]}.{int(parts[1]) + 1}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("master_file", help="docs/ master document to bump")
    ap.add_argument("--cross-iteration", action="store_true",
                    help="Major version bump for cross-iteration merge")
    args = ap.parse_args()

    _lib.debug_log(_S, "start", master=args.master_file, cross=args.cross_iteration)

    fm = _lib.parse_fm(args.master_file)
    if not fm:
        _lib.out_err(f"Cannot parse {args.master_file}")

    old_ver = str(fm.get("version", "1.0"))
    new_ver = _bump(old_ver, major=args.cross_iteration)
    today = date.today().isoformat()

    updates = {"version": new_ver, "updated-at": today}

    proc = fm.get("process", 0) or 0
    if proc in (3, 5) and fm.get("status") == "approved":
        pass
    else:
        updates["status"] = "draft"

    _lib.update_fm(args.master_file, updates)

    _lib.debug_log(_S, "done", old=old_ver, new=new_ver)
    _lib.out_json({
        "success": True,
        "file": _lib.norm(args.master_file),
        "old_version": old_ver,
        "new_version": new_ver,
        "updates": updates,
    })


if __name__ == "__main__":
    main()
