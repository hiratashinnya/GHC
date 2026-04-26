#!/usr/bin/env python3
"""M-2: detect-version-conflict — diff の base-version とマスター version の照合

責務:
    iter/ の diff ドキュメントの base-version と docs/ のマスタードキュメントの
    version を比較し、バージョン競合の有無を検証する。

入力:
    CLI 引数:
      diff_file   <path>  iter/ 内の diff ドキュメントパス
      master_file <path>  docs/ 内のマスタードキュメントパス

出力:
    JSON (stdout):
      { success, match, diff_base_version, master_version, message }
      success=True はバージョンが一致した場合のみ。

副作用:
    - detect_version_conflict.debug ファイルが存在する場合、
      detect_version_conflict.debug.log にログを追記する。
    - エラー時は { success: false, error } を stdout へ出力後 sys.exit(1)。

依存モジュール:
    - _lib (debug_log, parse_fm, out_err, out_json)
    - sys, os, argparse
"""
import sys, os, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib

_S = "M-2:detect-version-conflict"


def main():
    """diff とマスターのバージョンを照合せしまたは競合を検証する。

    責務:
        diff_file の base-version と master_file の version を比較し、
        一致時は success=True、不一致時はエラーメッセージ付きで出力する。

    入力:
        sys.argv:
          diff_file   <path>  iter/ 内の diff ドキュメント
          master_file <path>  docs/ 内のマスタードキュメント

    出力:
        stdout へ JSON を印字:
          { success, match, diff_base_version, master_version, message }

    副作用:
        - _lib.debug_log によりデバッグログを書き込む場合がある。
        - エラー時 _lib.out_err を通じて sys.exit(1) で終了する。

    依存モジュール:
        - _lib (debug_log, parse_fm, out_err, out_json)
        - argparse
    """
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
