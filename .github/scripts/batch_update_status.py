#!/usr/bin/env python3
"""R-2: batch-update-status — 複数ドキュメントのステータス・タグ・変更履歴一括更新

責務:
    指定した複数の Markdown ファイルの YAML フロントマターを一括更新する。
    status の変更、タグの追加、変更履歴行の追記を如意に並行実行できる。

入力:
    CLI 引数:
      --status <val>        設定するステータス値 (必須)
      --add-tags <t1,t2>    追加するタグ (カンマ区切り)
      --changelog <reason>  変更履歴の理由テキスト
      --version <str>       変更履歴のバージョン文字列
      --author <str>        変更履歴の担当者名
      files ...             更新対象ファイルリスト

出力:
    JSON (stdout):
      { success, data: [{ path, ok, reason? }] }

副作用:
    - 対象ファイルの YAML フロントマター (status, updated-at) を上書きする。
    - タグ指定時は tags 配列を更新する。
    - --changelog 指定時は変更履歴セクションに行を追記する。
    - batch_update_status.debug ファイルが存在する場合、
      batch_update_status.debug.log にログを追記する。

依存モジュール:
    - _lib (debug_log, update_fm, add_tags, append_changelog, out_json, norm)
    - sys, os, argparse, datetime.date
"""
import sys, os, argparse
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib

_S = "R-2:batch-update-status"


def main():
    """対象ファイルのステータス・タグ・変更履歴を一括更新し結果を JSON で出力する。

    責務:
        files に指定された全 Markdown ファイルに対して、status の上書き、
        タグ追加、変更履歴の追記を順で実行する。

    入力:
        sys.argv: --status, --add-tags, --changelog, --version, --author, files

    出力:
        stdout へ JSON を印字:
          { success, data: [{ path, ok, reason? }] }

    副作用:
        - 対象ファイルの YAML フロントマターを変更する。
        - --add-tags 時は tags 配列を更新する。
        - --changelog 時は変更履歴テーブルに行を追記する。
        - _lib.debug_log によりデバッグログを書き込む場合がある。

    依存モジュール:
        - _lib (debug_log, update_fm, add_tags, append_changelog, out_json, norm)
        - argparse, datetime.date
    """
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
