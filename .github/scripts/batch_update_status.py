#!/usr/bin/env python3
"""R-2: batch-update-status — Bulk-update status, tags, and changelog.

Usage:
  python batch_update_status.py --status <val> [--add-tags t1,t2]
         [--changelog "reason"] file1.md file2.md ...

Output: JSON  { success, data: [{ path, ok, reason? }] }
"""
import sys, os, argparse
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib

_S = "R-2:batch-update-status"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", required=True, help="New status value")
    ap.add_argument("--add-tags", help="Comma-separated tags to append")
    ap.add_argument("--changelog", help="Changelog entry reason")
    ap.add_argument("--version", default="", help="Version string for changelog entry")
    ap.add_argument("--author", default="", help="Author for changelog entry")
    ap.add_argument("files", nargs="+", help="Files to update")
    args = ap.parse_args()

    _lib.debug_log(_S, "start", status=args.status,
                   tags=args.add_tags, files=args.files)

    tags = [t.strip() for t in args.add_tags.split(",") if t.strip()] if args.add_tags else []
    today = date.today().isoformat()
    results = []

    for fp in args.files:
        fp = _lib.norm(fp)
        ok = _lib.update_fm(fp, {"status": args.status, "updated-at": today})
        if not ok:
            results.append({"path": fp, "ok": False, "reason": "fm_update_failed"})
            continue
        if tags:
            _lib.add_tags(fp, tags)
        if args.changelog:
            _lib.append_changelog(fp, today, args.changelog, args.version, args.author)
        results.append({"path": fp, "ok": True})

    success = all(r["ok"] for r in results)
    _lib.debug_log(_S, "done", updated=sum(1 for r in results if r["ok"]))
    _lib.out_json({"success": success, "data": results})


if __name__ == "__main__":
    main()
