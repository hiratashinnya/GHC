#!/usr/bin/env python3
"""U-1: parse-frontmatter — Bulk-parse YAML frontmatter from .md files.

Usage:
  python parse_frontmatter.py <directory>     # recursive scan
  python parse_frontmatter.py -f <file>       # single file

Output: JSON  { success, count, data: [{ _path, doc-type, status, ... }, ...] }
"""
import sys, os, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib

_S = "U-1:parse-frontmatter"


def main():
    ap = argparse.ArgumentParser(description="Parse YAML frontmatter from .md files")
    ap.add_argument("dir", nargs="?", help="Directory to scan recursively")
    ap.add_argument("-f", "--file", help="Parse a single file")
    args = ap.parse_args()

    _lib.debug_log(_S, "start", args=vars(args))

    if args.file:
        fm = _lib.parse_fm(args.file)
        if fm is None:
            _lib.out_err(f"No frontmatter in {args.file}")
        fm["_path"] = _lib.norm(args.file)
        data = [fm]
    elif args.dir:
        data = _lib.scan_fm(args.dir)
    else:
        _lib.out_err("Specify a directory or -f <file>")
        return

    _lib.debug_log(_S, "done", count=len(data))
    _lib.out_json({"success": True, "count": len(data), "data": data})


if __name__ == "__main__":
    main()
