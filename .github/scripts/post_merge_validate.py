#!/usr/bin/env python3
"""M-4: post-merge-validate — マージ後のマスタードキュメント検証

責務:
    マージ完了後の docs/ マスタードキュメントに対して以下を検証する。
    a) YAML フロントマターが解析可能で必須フィールドを持つ
    b) input-refs の展開先ファイルの存在とバージョン一致
    c) ドキュメント ID が正形式である

入力:
    CLI 引数:
      master_file <path>  検証対象の docs/ マスタードキュメントパス

出力:
    JSON (stdout):
      { success, file, issues, ids_found }

副作用:
    - post_merge_validate.debug ファイルが存在する場合、
      post_merge_validate.debug.log にログを追記する。
    - エラー時は { success: false, error } を stdout へ出力後 sys.exit(1)。

依存モジュール:
    - _lib (debug_log, parse_fm, read_text, out_json, norm)
    - sys, os, re, argparse
"""
import sys, os, re, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib

_S = "M-4:post-merge-validate"

_ID_PATTERNS = [
    r"REQ-F-\d+",
    r"REQ-NF-\d+",
    r"COMP-\d+",
    r"API-\w+",
    r"TBL-\w+",
    r"TC-\w+",
    r"RISK-\w+-\d+",
]

_REQUIRED_FIELDS = ["doc-type", "phase", "process", "iteration", "version", "status"]


def main():
    """master_file を多角的に検証し結果を JSON で出力する。

    責務:
        フロントマターの必須フィールド確認、input-refs の存在・バージョン検証、
        ドキュメント ID の抄出を実行し、検証結果を JSON で出力する。

    入力:
        sys.argv:
          master_file <path>  docs/ マスタードキュメントパス

    出力:
        stdout へ JSON を印字:
          { success, file, issues, ids_found }

    副作用:
        - _lib.debug_log によりデバッグログを書き込む場合がある。
        - エラー時 _lib.out_err を通じて sys.exit(1) で終了する。

    依存モジュール:
        - _lib (debug_log, parse_fm, read_text, out_json, norm)
        - re, argparse
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("master_file", help="docs/ master document to validate")
    args = ap.parse_args()

    _lib.debug_log(_S, "start", file=args.master_file)
    issues = []

    fm = _lib.parse_fm(args.master_file)
    if not fm:
        issues.append({"check": "frontmatter", "issue": "Cannot parse YAML frontmatter"})
        _lib.debug_log(_S, "done", ok=False)
        _lib.out_json({
            "success": False,
            "file": _lib.norm(args.master_file),
            "issues": issues,
            "ids_found": 0,
        })
        return

    for field in _REQUIRED_FIELDS:
        if field not in fm:
            issues.append({"check": "frontmatter", "issue": f"Missing field: {field}"})

    refs = fm.get("input-refs") or []
    base = os.path.dirname(args.master_file)
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        rp = ref.get("path", "")
        resolved = _lib.norm(os.path.normpath(os.path.join(base, rp)))
        if not os.path.exists(resolved):
            issues.append({"check": "input-refs", "ref": rp, "issue": "not_found"})
        elif ref.get("version"):
            tfm = _lib.parse_fm(resolved)
            if tfm and str(tfm.get("version", "")) != str(ref["version"]):
                issues.append({
                    "check": "input-refs", "ref": rp,
                    "issue": "version_mismatch",
                    "expected": str(ref["version"]),
                    "actual": str(tfm.get("version", "")),
                })

    text = _lib.read_text(args.master_file) or ""
    found_ids = set()
    for pat in _ID_PATTERNS:
        found_ids.update(re.findall(pat, text))

    ok = len(issues) == 0
    _lib.debug_log(_S, "done", ok=ok, issues=len(issues), ids=len(found_ids))
    _lib.out_json({
        "success": ok,
        "file": _lib.norm(args.master_file),
        "issues": issues,
        "ids_found": len(found_ids),
    })


if __name__ == "__main__":
    main()
