#!/usr/bin/env python3
"""U-1: parse-frontmatter — Markdown ファイルから YAML フロントマターを一括解析

責務:
    指定ディレクトリ（再帰スキャン）または単一ファイルから YAML フロントマターを
    解析し、パス情報付きのディクショナリリストとして出力する。

入力:
    CLI 引数:
      dir <path>    再帰スキャン対象ディレクトリ
      -f <path>     単一ファイルパス

出力:
    JSON (stdout):
      { success, count, data: [{ _path, doc-type, status, ... }, ...] }

副作用:
    - parse_frontmatter.debug ファイルが存在する場合、
      parse_frontmatter.debug.log にログを追記する。
    - エラー時は { success: false, error } を stdout へ出力後 sys.exit(1)。

依存モジュール:
    - _lib (debug_log, parse_fm, scan_fm, out_err, out_json, norm)
    - sys, os, argparse
"""
import sys, os, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib

_S = "U-1:parse-frontmatter"


def main():
    """YAML フロントマターを解析し結果を JSON で出力する。

    責務:
        -f または dir 引数に応じて単一ファイル・ディレクトリを解析し、
        data 配列を JSON で stdout に出力する。

    入力:
        sys.argv:
          dir <path>   再帰スキャン対象ディレクトリ
          -f <path>    単一ファイルパス

    出力:
        stdout へ JSON を印字:
          { success, count, data: [{ _path, doc-type, status, ... }] }

    副作用:
        - _lib.debug_log によりデバッグログを書き込む場合がある。
        - 引数未指定時onエラー時 _lib.out_err を通じて sys.exit(1) で終了する。

    依存モジュール:
        - _lib (debug_log, parse_fm, scan_fm, out_err, out_json, norm)
        - argparse
    """
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
