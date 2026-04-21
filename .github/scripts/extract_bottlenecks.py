#!/usr/bin/env python3
"""D-2: extract-bottlenecks — Find blocked / rejected / under-revision docs.

Usage:
  python extract_bottlenecks.py [--docs-dir docs]

Output: JSON  { success, count, markdown, items }
"""
import sys, os, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib

_S = "D-2:extract-bottlenecks"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs-dir", default="docs", help="Root docs directory")
    args = ap.parse_args()

    _lib.debug_log(_S, "start", docs=args.docs_dir)

    items = _lib.find_bottleneck_lines(args.docs_dir)
    md = "\n".join(items) if items else "- なし"

    _lib.debug_log(_S, "done", count=len(items))
    _lib.out_json({
        "success": True,
        "count": len(items),
        "markdown": md,
        "items": items,
    })


if __name__ == "__main__":
    main()
