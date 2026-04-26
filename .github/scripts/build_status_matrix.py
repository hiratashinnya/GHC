#!/usr/bin/env python3
"""D-1: build-status-matrix — ダッシュボード用ステータスマトリクス生成

責務:
    docs/ 配下の各フェーズ・プロセスドキュメントのステータスを読み取り、
    ダッシュボード Markdown に埋め込むステータスマトリクスとコンポーネントテーブルを生成する。

入力:
    CLI 引数:
      --docs-dir <path>  docs ルートディレクトリ (デフォルト: docs)

出力:
    JSON (stdout):
      { success, matrix, component_table }
      matrix         : ステータスマトリクス Markdown 文字列
      component_table: 詳細設計コンポーネント進捗テーブル (None の場合あり)

副作用:
    - build_status_matrix.debug ファイルが存在する場合、
      build_status_matrix.debug.log にログを追記する。

依存モジュール:
    - _lib (debug_log, build_status_matrix_md, build_component_table_md, out_json)
    - sys, os, argparse
"""
import sys, os, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib

_S = "D-1:build-status-matrix"


def main():
    """docs/ ディレクトリをスキャンしステータスマトリクスを JSON に出力する。

    責務:
        --docs-dir 内の全フェーズドキュメントのステータスを聯結して
        Markdown 形式のステータスマトリクスとコンポーネントテーブルを生成する。

    入力:
        sys.argv:
          --docs-dir <path>  docs ルートディレクトリ

    出力:
        stdout へ JSON を印字:
          { success, matrix, component_table }

    副作用:
        - _lib.debug_log によりデバッグログを書き込む場合がある。

    依存モジュール:
        - _lib (debug_log, build_status_matrix_md, build_component_table_md, out_json)
        - argparse
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs-dir", default="docs", help="Root docs directory")
    args = ap.parse_args()

    _lib.debug_log(_S, "start", docs=args.docs_dir)

    matrix = _lib.build_status_matrix_md(args.docs_dir)
    comp = _lib.build_component_table_md(args.docs_dir)

    _lib.debug_log(_S, "done")
    _lib.out_json({
        "success": True,
        "matrix": matrix,
        "component_table": comp,
    })


if __name__ == "__main__":
    main()
