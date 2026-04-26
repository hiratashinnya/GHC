#!/usr/bin/env python3
"""R-1: resolve-cascade-scope — ロールバックにより影響を受けるダウンストリーム文書の列挙

責務:
    ロールバック対象ファイルのフェーズ・プロセス番号を基に、
    同一フェーズ内の後続プロセスおよび --ng-phase 指定時は
    クロスフェーズの全ドキュメントをダウンストリーム候補として返す。

入力:
    CLI 引数:
      --target  <path>   ロールバック対象ファイルパス
      --ng-phase <phase>  NG 発生フェーズ (クロスフェーズ時に指定)

出力:
    JSON (stdout):
      { success, target, cross_phase, downstream: [{ path, status }], count }

副作用:
    - resolve_cascade_scope.debug ファイルが存在する場合、
      resolve_cascade_scope.debug.log にログを追記する。
    - エラー時は { success: false, error } を stdout へ出力後 sys.exit(1)。

依存モジュール:
    - _lib (debug_log, parse_fm, phase_path, list_dd_components, out_err, out_json, norm,
            DD_OVERVIEW, PROC_FILE, DD_VALIDATION)
    - sys, os, argparse, pathlib.Path
"""
import sys, os, argparse
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib

_S = "R-1:resolve-cascade-scope"

_SKIP = ("rejected", "under-revision")


def _collect_phase(phase, min_proc, docs="docs"):
    """指定フェーズ内で process > min_proc の未無効化ドキュメントを列挙する。

    責務:
        指定フェーズのプロセスドキュメントから min_proc を超えるものを探し、
        status が rejected / under-revision でないドキュメントを返す。
        detailed-design フェーズは検証ファイルとコンポーネントドキュメントも対象に含む。

    入力:
        phase (str)  : フェーズ名 (例: "requirements")。
        min_proc (int): こ超える process 番号の閾値。
        docs (str)   : docs ルートディレクトリ (デフォルト: "docs")。

    出力:
        list[dict]: [{ path: str, status: str }, ...]。

    副作用:
        なし。

    依存モジュール:
        - _lib (phase_path, parse_fm, list_dd_components, DD_OVERVIEW, PROC_FILE, DD_VALIDATION, norm)
        - os
    """
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
    """指定フェーズの全ドキュメントを特定のプロセス制限なしで列挙する。

    責務:
        min_proc=0 で _collect_phase を呢び出し、フェーズ内の全ドキュメントを返す。

    入力:
        phase (str) : フェーズ名。
        docs (str)  : docs ルートディレクトリ (デフォルト: "docs")。

    出力:
        list[dict]: [{ path: str, status: str }, ...]。

    副作用:
        なし。

    依存モジュール:
        - _collect_phase (同モジュール内)。
    """
    return _collect_phase(phase, 0, docs)


def main():
    """ロールバックのカスケードスコープを解決しダウンストリーム一覧を JSON で出力する。

    責務:
        --target のフェーズ・プロセス番号を基に後続ドキュメントを収集し、
        --ng-phase が異なるフェーズの場合はクロスフェーズ列挙も実行する。
        重複を除去した一意履歴を JSON で出力する。

    入力:
        sys.argv:
          --target <path>    ロールバック対象ファイルパス
          --ng-phase <phase>  NG 発生フェーズ

    出力:
        stdout へ JSON を印字:
          { success, target, cross_phase, downstream: [{ path, status }], count }

    副作用:
        - _lib.debug_log によりデバッグログを書き込む場合がある。
        - エラー時 _lib.out_err を通じて sys.exit(1) で終了する。

    依存モジュール:
        - _lib (debug_log, parse_fm, out_err, out_json, norm)
        - argparse, pathlib.Path
    """
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
