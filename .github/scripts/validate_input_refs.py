#!/usr/bin/env python3
"""U-2: validate-input-refs — input-refs のパス存在およびバージョン服表検証

責務:
    各 Markdown ファイルの YAML フロントマター内 input-refs を読み取り、
    参照先パスの存在とバージョン朝山を検証する。

入力:
    CLI 引数:
      dir <path>   検証対象ディレクトリ (再帰スキャン)
      -f <path>    検証対象単一ファイル

出力:
    JSON (stdout):
      { success, data: [{ path, ok, checked, issues }, ...] }

副作用:
    - validate_input_refs.debug ファイルが存在する場合、
      validate_input_refs.debug.log にログを追記する。
    - エラー時は { success: false, error } を stdout へ出力後 sys.exit(1)。

依存モジュール:
    - _lib (debug_log, parse_fm, scan_fm, out_err, out_json, norm)
    - sys, os, argparse
"""
import sys, os, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib

_S = "U-2:validate-input-refs"


def check_one(fpath):
    """単一ファイルの input-refs を検証し結果ディクショナリを返す。

    責務:
        fpath の YAML フロントマターから input-refs を取得し、
        各参照のパス存在とバージョン一致を検証する。

    入力:
        fpath (str): 検証対象の Markdown ファイルパス。

    出力:
        dict: { path, ok, checked, issues }
              フロントマターなしの場合 { path, skip: True }。

    副作用:
        なし。

    依存モジュール:
        - _lib (parse_fm, norm)
        - os
    """
    fm = _lib.parse_fm(fpath)
    if not fm:
        return {"path": _lib.norm(fpath), "skip": True}
    refs = fm.get("input-refs") or []
    issues = []
    base = os.path.dirname(fpath)
    for r in refs:
        if not isinstance(r, dict):
            continue
        rp = r.get("path", "")
        rv = r.get("version")
        resolved = _lib.norm(os.path.normpath(os.path.join(base, rp)))
        if not os.path.exists(resolved):
            issues.append({"ref": rp, "issue": "not_found", "resolved": resolved})
            continue
        if rv is not None:
            tfm = _lib.parse_fm(resolved)
            if tfm and str(tfm.get("version", "")) != str(rv):
                issues.append({
                    "ref": rp, "issue": "version_mismatch",
                    "expected": str(rv), "actual": str(tfm.get("version", "")),
                })
    return {
        "path": _lib.norm(fpath),
        "ok": len(issues) == 0,
        "checked": len(refs),
        "issues": issues,
    }


def main():
    """input-refs を検証し結果を JSON で出力する。

    責務:
        -f または dir 引数に応じて対象ファイルを解決し、check_one を寄び集め、
        総合成功フラグと結果配列を JSON で stdout に出力する。

    入力:
        sys.argv:
          dir <path>   対象ディレクトリ
          -f <path>    対象単一ファイル

    出力:
        stdout へ JSON を印字:
          { success, data: [{ path, ok, checked, issues }] }

    副作用:
        - _lib.debug_log によりデバッグログを書き込む場合がある。
        - 引数未指定時 _lib.out_err を通じて sys.exit(1) で終了する。

    依存モジュール:
        - _lib (debug_log, scan_fm, out_err, out_json)
        - argparse
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("dir", nargs="?")
    ap.add_argument("-f", "--file")
    args = ap.parse_args()

    _lib.debug_log(_S, "start", args=vars(args))

    if args.file:
        results = [check_one(args.file)]
    elif args.dir:
        results = [check_one(f["_path"]) for f in _lib.scan_fm(args.dir)]
    else:
        _lib.out_err("Specify a directory or -f <file>")
        return

    ok = all(r.get("ok", True) for r in results if not r.get("skip"))
    _lib.debug_log(_S, "done", total=len(results), all_ok=ok)
    _lib.out_json({"success": ok, "data": results})


if __name__ == "__main__":
    main()
