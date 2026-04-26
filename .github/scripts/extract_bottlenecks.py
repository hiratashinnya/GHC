#!/usr/bin/env python3
"""D-2: extract-bottlenecks — ブロック・差し戻し・承認待ちドキュメントの抽出

責務:
    docs/ 配下の全 Markdown ファイルをスキャンし、status が
    rejected / under-revision 、または approval-required で未承認の
    ドキュメントをボトルネックとしてリストアップする。

入力:
    CLI 引数:
      --docs-dir <path>  docs ルートディレクトリ (デフォルト: docs)

出力:
    JSON (stdout):
      { success, count, markdown, items }
      markdown: Markdown 形式の箇条書き文字列
      items   : 個別箇条文字列のリスト

副作用:
    - extract_bottlenecks.debug ファイルが存在する場合、
      extract_bottlenecks.debug.log にログを追記する。

依存モジュール:
    - _lib (debug_log, find_bottleneck_lines, out_json)
    - sys, os, argparse
"""
import sys, os, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib

_S = "D-2:extract-bottlenecks"


def main():
    """docs/ をスキャンしてボトルネックドキュメントを JSON で出力する。

    責務:
        find_bottleneck_lines の結果を Markdown 箇条形式に整形し、
        items リストとともに JSON で stdout に出力する。

    入力:
        sys.argv:
          --docs-dir <path>  docs ルートディレクトリ

    出力:
        stdout へ JSON を印字:
          { success, count, markdown, items }

    副作用:
        - _lib.debug_log によりデバッグログを書き込む場合がある。

    依存モジュール:
        - _lib (debug_log, find_bottleneck_lines, out_json)
        - argparse
    """
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
