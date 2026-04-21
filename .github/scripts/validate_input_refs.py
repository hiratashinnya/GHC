#!/usr/bin/env python3
"""U-2: validate-input-refs — Check input-refs paths exist & versions match.

Usage:
  python validate_input_refs.py <directory>
  python validate_input_refs.py -f <file>

Output: JSON  { success, data: [{ path, ok, checked, issues }, ...] }
"""
import sys, os, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib

_S = "U-2:validate-input-refs"


def check_one(fpath):
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
