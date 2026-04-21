#!/usr/bin/env python3
"""R-1: resolve-cascade-scope — List downstream docs affected by rollback.

Usage:
  python resolve_cascade_scope.py --target <file> [--ng-phase <phase>]

Output: JSON  { success, target, cross_phase, downstream: [{ path, status }], count }
"""
import sys, os, argparse
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib

_S = "R-1:resolve-cascade-scope"

_SKIP = ("rejected", "under-revision")


def _collect_phase(phase, min_proc, docs="docs"):
    """Existing docs in *phase* with process > min_proc, not already invalidated."""
    out = []
    pp = _lib.phase_path(phase, docs)
    fmap = _lib.DD_OVERVIEW if phase == "detailed-design" else _lib.PROC_FILE

    for p, fn in sorted(fmap.items()):
        if p <= min_proc:
            continue
        fp = _lib.norm(os.path.join(pp, fn))
        if not os.path.exists(fp):
            continue
        fm = _lib.parse_fm(fp)
        if fm and fm.get("status") not in _SKIP:
            out.append({"path": fp, "status": fm.get("status", "")})

    if phase == "detailed-design":
        if min_proc < 3:
            vf = _lib.norm(os.path.join(pp, _lib.DD_VALIDATION))
            if os.path.exists(vf):
                fm = _lib.parse_fm(vf)
                if fm and fm.get("status") not in _SKIP:
                    out.append({"path": vf, "status": fm.get("status", "")})
        for cf in _lib.list_dd_components(docs):
            fm = _lib.parse_fm(cf)
            if fm and (fm.get("process", 0) or 0) > min_proc:
                if fm.get("status") not in _SKIP:
                    out.append({"path": cf, "status": fm.get("status", "")})
    return out


def _collect_all(phase, docs="docs"):
    return _collect_phase(phase, 0, docs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True, help="Rollback target file path")
    ap.add_argument("--ng-phase", help="Phase where NG was issued (cross-phase)")
    args = ap.parse_args()

    _lib.debug_log(_S, "start", target=args.target, ng_phase=args.ng_phase)
    tp = _lib.norm(args.target)

    fm = _lib.parse_fm(tp)
    if not fm:
        _lib.out_err(f"Cannot parse frontmatter: {tp}")

    tphase = fm.get("phase", "")
    tproc = fm.get("process", 0) or 0
    ng_phase = args.ng_phase or tphase
    is_cross = ng_phase != tphase
    is_dd_comp = tphase == "detailed-design" and "/components/" in tp

    downstream = []

    if is_dd_comp:
        cdir = os.path.dirname(tp)
        for f in sorted(Path(cdir).glob("*.md")):
            fp = _lib.norm(f)
            if fp == tp:
                continue
            cfm = _lib.parse_fm(fp)
            if cfm and (cfm.get("process", 0) or 0) > tproc:
                if cfm.get("status") not in _SKIP:
                    downstream.append({"path": fp, "status": cfm.get("status", "")})
        pp = _lib.phase_path("detailed-design")
        vf = _lib.norm(os.path.join(pp, _lib.DD_VALIDATION))
        if os.path.exists(vf):
            vfm = _lib.parse_fm(vf)
            if vfm and vfm.get("status") not in _SKIP:
                downstream.append({"path": vf, "status": vfm.get("status", "")})
    else:
        downstream += _collect_phase(tphase, tproc)

    if is_cross:
        downstream += _collect_all(ng_phase)

    seen = set()
    unique = []
    for d in downstream:
        if d["path"] not in seen and d["path"] != tp:
            seen.add(d["path"])
            unique.append(d)

    _lib.debug_log(_S, "done", count=len(unique))
    _lib.out_json({
        "success": True,
        "target": {"path": tp, "phase": tphase, "process": tproc},
        "cross_phase": is_cross,
        "downstream": unique,
        "count": len(unique),
    })


if __name__ == "__main__":
    main()
