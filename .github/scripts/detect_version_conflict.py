#!/usr/bin/env python3
"""M-2: detect-version-conflict — Compare diff base-version with master version.

Usage:
  python detect_version_conflict.py <diff_file> <master_file>

Output: JSON  { success, match, diff_base_version, master_version, message }
"""
import sys, os, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib

_S = "M-2:detect-version-conflict"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("diff_file", help="iter/ diff document")
    ap.add_argument("master_file", help="docs/ master document")
    args = ap.parse_args()

    _lib.debug_log(_S, "start", diff=args.diff_file, master=args.master_file)

    dfm = _lib.parse_fm(args.diff_file)
    if not dfm:
        _lib.out_err(f"Cannot parse {args.diff_file}")

    mfm = _lib.parse_fm(args.master_file)
    if not mfm:
        _lib.out_err(f"Cannot parse {args.master_file}")

    bv = str(dfm.get("base-version", ""))
    mv = str(mfm.get("version", ""))
    match = bv == mv

    msg = "" if match else (
        f"Version conflict: diff base-version '{bv}' != master version '{mv}'"
    )

    _lib.debug_log(_S, "done", match=match, base=bv, master=mv)
    _lib.out_json({
        "success": match,
        "match": match,
        "diff_base_version": bv,
        "master_version": mv,
        "message": msg,
    })


if __name__ == "__main__":
    main()
