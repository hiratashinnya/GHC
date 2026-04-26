#!/usr/bin/env python3
"""M-3: bump-version — マージ後のマスターバージョンインクリメント

責務:
    マージ完了後に docs/ 内のマスタードキュメントの version をインクリメントし、
    updated-at ・ status を更新する。

入力:
    CLI 引数:
      master_file <path>      更新対象の docs/ マスタードキュメントパス
      --cross-iteration       イテレーション跨ぎマージ時にメイジャーバージョンアップする

出力:
    JSON (stdout):
      { success, file, old_version, new_version, updates }
    ルール:
      プロセス ①②④  → minor インクリメント (1.0 → 1.1), status = draft
      プロセス ③⑤   → minor インクリメント, 既に approved なら status を維持
      --cross-iteration → major インクリメント (1.x → 2.0)

副作用:
    - フロントマターの version / updated-at / status フィールドを上書きする。
    - bump_version.debug ファイルが存在する場合、
      bump_version.debug.log にログを追記する。
    - エラー時は { success: false, error } を stdout へ出力後 sys.exit(1)。

依存モジュール:
    - _lib (debug_log, parse_fm, update_fm, out_err, out_json, norm)
    - sys, os, argparse, datetime.date
"""
import sys, os, argparse
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib

_S = "M-3:bump-version"


def _bump(version_str, major=False):
    """version 文字列をインクリメントした安定版を返す。

    責務:
        ""."."区切りのバージョン文字列を解析し、major フラグに応じて
        メイジャーまたはマイナーをインクリメントする。

    入力:
        version_str (str): "メイジャー.マイナー" 形式のバージョン文字列。
        major (bool)     : True の場合はメイジャーを +1 しマイナーを 0 にリセット。

    出力:
        str: インクリメント後のバージョン文字列。

    副作用:
        なし。

    依存モジュール:
        なし (組み込み型のみ)。
    """
    parts = str(version_str).split(".")
    if len(parts) < 2:
        parts = [parts[0], "0"]
    if major:
        return f"{int(parts[0]) + 1}.0"
    return f"{parts[0]}.{int(parts[1]) + 1}"


def main():
    """CLI 引数を解析しバージョンをインクリメントしフロントマターを更新する。

    責務:
        master_file のフロントマターから現在の version を読み取り、_bump() で
        新バージョンを計算して _lib.update_fm でファイルを更新する。

    入力:
        sys.argv:
          master_file <path>  docs/ マスタードキュメントパス
          --cross-iteration   イテレーション跨ぎマージ指定フラグ

    出力:
        stdout へ JSON を印字:
          { success, file, old_version, new_version, updates }

    副作用:
        - master_file の YAML フロントマター (version, updated-at, status) を上書きする。
        - _lib.debug_log によりデバッグログを書き込む場合がある。
        - エラー時 _lib.out_err を通じて sys.exit(1) で終了する。

    依存モジュール:
        - _lib (debug_log, parse_fm, update_fm, out_err, out_json, norm)
        - argparse, datetime.date
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("master_file", help="docs/ master document to bump")
    ap.add_argument("--cross-iteration", action="store_true",
                    help="Major version bump for cross-iteration merge")
    args = ap.parse_args()

    _lib.debug_log(_S, "start", master=args.master_file, cross=args.cross_iteration)

    fm = _lib.parse_fm(args.master_file)
    if not fm:
        _lib.out_err(f"Cannot parse {args.master_file}")

    old_ver = str(fm.get("version", "1.0"))
    new_ver = _bump(old_ver, major=args.cross_iteration)
    today = date.today().isoformat()

    updates = {"version": new_ver, "updated-at": today}

    proc = fm.get("process", 0) or 0
    if proc in (3, 5) and fm.get("status") == "approved":
        pass
    else:
        updates["status"] = "draft"

    _lib.update_fm(args.master_file, updates)

    _lib.debug_log(_S, "done", old=old_ver, new=new_ver)
    _lib.out_json({
        "success": True,
        "file": _lib.norm(args.master_file),
        "old_version": old_ver,
        "new_version": new_ver,
        "updates": updates,
    })


if __name__ == "__main__":
    main()
