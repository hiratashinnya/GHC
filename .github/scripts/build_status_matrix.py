#!/usr/bin/env python3
"""D-1: build-status-matrix — Generate dashboard status matrix Markdown.

Usage:
  python build_status_matrix.py [--docs-dir docs]

Output: JSON  { success, matrix, component_table }
"""
import sys, os, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib

_S = "D-1:build-status-matrix"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs-dir", default="docs", help="Root docs directory")
    args = ap.parse_args()

    _lib.debug_log(_S, "start", docs=args.docs_dir)

    matrix = _lib.build_matrix_md(args.docs_dir)
    comp = _lib.build_component_table_md(args.docs_dir)

    _lib.debug_log(_S, "done")
    _lib.out_json({
        "success": True,
        "matrix": matrix,
        "component_table": comp,
    })


if __name__ == "__main__":
    main()
