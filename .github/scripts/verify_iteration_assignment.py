#!/usr/bin/env python3
"""I-2: verify-iteration-assignment — 全 REQ-F のイテレーション割り当て検証

責務:
    breakdown ドキュメントの全 REQ-F ID がイテレーションファイルに
    割り当てられているか、重複がないか、input-refs が解決するかを検証する。

入力:
    CLI 引数:
      --iterations-dir <path>  イテレーション成果物ディレクトリ
                               (デフォルト: docs/requirements/iterations)
      --breakdown <path>       定義元の要件分解ドキュメント
                               (デフォルト: docs/requirements/02-breakdown.md)

出力:
    JSON (stdout):
      { success, total_reqs, assigned_reqs, unassigned, issues }

副作用:
    - verify_iteration_assignment.debug ファイルが存在する場合、
      verify_iteration_assignment.debug.log にログを追記する。

依存モジュール:
    - _lib (debug_log, read_text, parse_fm, out_json, norm)
    - sys, os, re, argparse, pathlib.Path
"""
import sys, os, re, argparse
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib

_S = "I-2:verify-iteration-assignment"


def main():
    """全 REQ-F のイテレーション割り当てを検証し結果を JSON で出力する。

    責務:
        breakdown から全 REQ-F を抽出し、イテレーションファイルの割り当て状況を
        照合して未割り当て・重複・ input-refs 不整合を検証する。

    入力:
        sys.argv:
          --iterations-dir <path>  iterations ディレクトリ
          --breakdown <path>       分解ドキュメントパス

    出力:
        stdout へ JSON を印字:
          { success, total_reqs, assigned_reqs, unassigned, issues }

    副作用:
        - _lib.debug_log によりデバッグログを書き込む場合がある。

    依存モジュール:
        - _lib (debug_log, read_text, parse_fm, out_json, norm)
        - re, argparse, pathlib.Path
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--iterations-dir", default="docs/requirements/iterations",
                    help="Directory containing iteration artifact files")
    ap.add_argument("--breakdown", default="docs/requirements/02-breakdown.md",
                    help="Breakdown document with all REQ-F definitions")
    args = ap.parse_args()

    _lib.debug_log(_S, "start", idir=args.iterations_dir, bd=args.breakdown)

    bd_text = _lib.read_text(args.breakdown) or ""
    all_reqs = set(re.findall(r"REQ-F-\d+", bd_text))

    idir = Path(args.iterations_dir)
    assigned = {}
    duplicates = []
    issues = []

    if idir.exists():
        for fp in sorted(idir.glob("*.md")):
            text = _lib.read_text(str(fp)) or ""
            reqs = set(re.findall(r"REQ-F-\d+", text))
            for r in reqs:
                if r in assigned:
                    duplicates.append({
                        "req": r,
                        "files": [assigned[r], _lib.norm(fp)],
                    })
                else:
                    assigned[r] = _lib.norm(fp)

    unassigned = sorted(all_reqs - set(assigned.keys()))
    if unassigned:
        issues.append({"issue": "unassigned_reqs", "reqs": unassigned})
    if duplicates:
        issues.append({"issue": "duplicate_assignments", "duplicates": duplicates})

    if idir.exists():
        for fp in sorted(idir.glob("*.md")):
            fm = _lib.parse_fm(str(fp))
            if not fm:
                continue
            for ref in (fm.get("input-refs") or []):
                if not isinstance(ref, dict):
                    continue
                rp = ref.get("path", "")
                resolved = os.path.normpath(os.path.join(str(fp.parent), rp))
                if not os.path.exists(resolved):
                    issues.append({
                        "issue": "input_ref_missing",
                        "file": _lib.norm(fp),
                        "ref": rp,
                    })

    ok = len(issues) == 0
    _lib.debug_log(_S, "done", ok=ok, total=len(all_reqs), assigned=len(assigned))
    _lib.out_json({
        "success": ok,
        "total_reqs": len(all_reqs),
        "assigned_reqs": len(assigned),
        "unassigned": unassigned,
        "issues": issues,
    })


if __name__ == "__main__":
    main()
