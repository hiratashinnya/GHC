#!/usr/bin/env python3
"""M-1: check-merge-prerequisites — diff ドキュメントのマージ履行条件検証

責務:
    iter/ 配下の diff ドキュメントの YAML フロントマターを検証し、
    マージ実行の前提条件（ステータス・ doc-kind ・バージョン・承認情報）を満たしているかを確認する。

入力:
    CLI 引数:
      diff_file <path>  検証対象の iter/ 内 diff ドキュメントパス

出力:
    JSON (stdout):
      { success, file, issues }

副作用:
    - check_merge_prerequisites.debug ファイルが存在する場合、
      check_merge_prerequisites.debug.log にログを追記する。
    - エラー時は { success: false, error } を stdout へ出力後 sys.exit(1)。

依存モジュール:
    - _lib (debug_log, parse_fm, out_err, out_json, norm)
    - sys, os, argparse
"""
import sys, os, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib

_S = "M-1:check-merge-prerequisites"


def main():
    """diff ドキュメントのフロントマターを検証し結果を JSON で出力する。

    責務:
        diff_file の YAML フロントマターを解析し、status / doc-kind /
        base-version / 承認情報の各項目を検証する。

    入力:
        sys.argv:
          diff_file <path>  iter/ 内の diff ドキュメントパス

    出力:
        stdout へ JSON を印字:
          { success, file, issues }
          success=True は issues が空の場合のみ。

    副作用:
        - _lib.debug_log によりデバッグログを書き込む場合がある。
        - エラー時 _lib.out_err を通じて sys.exit(1) で終了する。

    依存モジュール:
        - _lib (debug_log, parse_fm, out_err, out_json, norm)
        - argparse
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("diff_file", help="Path to the diff document in iter/")
    args = ap.parse_args()

    _lib.debug_log(_S, "start", diff=args.diff_file)

    fm = _lib.parse_fm(args.diff_file)
    if not fm:
        _lib.out_err(f"Cannot parse frontmatter: {args.diff_file}")

    issues = []

    if fm.get("status") != "approved":
        issues.append(f"status is '{fm.get('status')}', expected 'approved'")
    if fm.get("doc-kind") != "diff":
        issues.append(f"doc-kind is '{fm.get('doc-kind')}', expected 'diff'")
    if fm.get("base-version") is None:
        issues.append("base-version is missing")
    if fm.get("approval-required"):
        if not fm.get("approved-by"):
            issues.append("approval-required but approved-by is empty")
        if not fm.get("approved-at"):
            issues.append("approval-required but approved-at is empty")

    ok = len(issues) == 0
    _lib.debug_log(_S, "done", ok=ok, issues=issues)
    _lib.out_json({
        "success": ok,
        "file": _lib.norm(args.diff_file),
        "issues": issues,
    })


if __name__ == "__main__":
    main()
