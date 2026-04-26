#!/usr/bin/env python3
"""Scan iter/ for approved but not-yet-merged diff documents.

責務:
    iter/ 配下の全 .md ファイルを走査し、doc-kind: diff かつ status: approved で
    対応する docs/ 正本にまだマージされていないドキュメントを検出する。

入力:
    CLI 引数:
      --iter-dir  <path>  iter ルートディレクトリ (デフォルト: iter)
      --docs-dir  <path>  docs ルートディレクトリ (デフォルト: docs)

出力:
    JSON (stdout):
      {
        "unmerged": [
          {
            "diff_path":    "iter/iter1/phase2/04-artifact.md",
            "master_path":  "docs/basic-design/04-artifact.md",
            "phase":        "basic-design",
            "process":      4,
            "iteration":    1,
            "base_version": "1.0"
          },
          ...
        ],
        "total": <N>
      }

副作用:
    - scan_unmerged_diffs.debug ファイルが存在する場合、
      scan_unmerged_diffs.debug.log にログを追記する。
    - エラー時は { success: false, error } を stdout へ出力後 sys.exit(1)。

依存モジュール:
    - _lib (debug_log, out_err, out_json, parse_fm)
    - sys, os, glob, argparse
"""
import sys
import os
import glob
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib

_S = "scan-unmerged-diffs"

# iter/phaseN → docs/<phase-dir> マッピング
PHASE_MAP = {
    "phase1": "requirements",
    "phase2": "basic-design",
    "phase3": "detailed-design",
    "phase4": "implementation",
    "phase5": "testing",
    "phase6": "release",
}

# プロセスファイル名プレフィックス → プロセス番号 (例: "04-artifact.md" → 4)
_PROC_PREFIX = {str(i).zfill(2): i for i in range(1, 6)}


def _parse_version(v):
    """バージョン文字列 "1.2" を (1, 2) に変換する。

    責務:
        "major.minor" 形式のバージョン文字列を整数タプルにパースする。
        不正値の場合は (0, 0) を返す。

    入力:
        v (str | int | float | None): バージョン値。

    出力:
        tuple[int, int]: (major, minor) タプル。

    副作用:
        なし。
    """
    try:
        parts = str(v).split(".")
        return tuple(int(x) for x in parts[:2]) if len(parts) >= 2 else (int(parts[0]), 0)
    except (ValueError, TypeError):
        return (0, 0)


def _resolve_master_path(diff_path, iter_dir, docs_dir):
    """差分ファイルパスから対応する正本ファイルパスを導出する。

    責務:
        iter/<iterN>/<phaseK>/... のパス構造を解析し、
        PHASE_MAP を使って docs/<phase-dir>/... の正本パスを生成する。

    入力:
        diff_path (str): 差分ファイルの相対パス (iter_dir 起点)。
        iter_dir  (str): iter ルートディレクトリ。
        docs_dir  (str): docs ルートディレクトリ。

    出力:
        str | None: 正本ファイルパス。phaseN が PHASE_MAP に存在しない場合は None。

    副作用:
        なし。
    """
    # diff_path は絶対パスの場合もあるため相対化
    abs_iter = os.path.abspath(iter_dir)
    abs_diff = os.path.abspath(diff_path)
    try:
        rel = os.path.relpath(abs_diff, abs_iter)  # iter1/phase2/foo.md
    except ValueError:
        return None

    parts = rel.replace("\\", "/").split("/")
    # parts[0] = "iter1", parts[1] = "phase2", parts[2:] = ["foo.md"] or ["components", ...]
    if len(parts) < 3:
        return None

    phase_key = parts[1]
    phase_dir = PHASE_MAP.get(phase_key)
    if phase_dir is None:
        return None

    sub_path = os.path.join(*parts[2:])
    return os.path.join(docs_dir, phase_dir, sub_path)


def _extract_process_number(filename):
    """ファイル名からプロセス番号を返す。

    責務:
        "04-artifact.md" のように先頭 2 桁がプロセス番号であるファイル名を
        整数に変換する。判定不能時は None。

    入力:
        filename (str): ファイル名 (パスを含まない basename)。

    出力:
        int | None: プロセス番号 (1〜5)、または None。

    副作用:
        なし。
    """
    prefix = os.path.basename(filename)[:2]
    return _PROC_PREFIX.get(prefix)


def _is_unmerged(diff_fm, master_path):
    """差分がまだ正本にマージされていないかどうかを判定する。

    責務:
        正本ファイルが存在しない場合は未マージとみなす。
        存在する場合は master.version <= diff.base-version であれば未マージ。

    入力:
        diff_fm     (dict): 差分ファイルのフロントマター。
        master_path (str):  対応する正本ファイルのパス。

    出力:
        bool: 未マージであれば True。

    副作用:
        なし。
    """
    if not os.path.exists(master_path):
        return True
    master_fm = _lib.parse_fm(master_path)
    if not master_fm:
        return True
    base = _parse_version(diff_fm.get("base-version"))
    cur = _parse_version(master_fm.get("version", "0.0"))
    return cur <= base


def scan(iter_dir, docs_dir):
    """未マージ承認済み差分ドキュメントを走査して一覧を返す。

    責務:
        iter/ 配下の全 .md ファイルを glob で収集し、
        doc-kind: diff かつ status: approved のファイルを絞り込んだ後、
        _is_unmerged で正本との照合を行い未マージ一覧を返す。

    入力:
        iter_dir (str): iter ルートディレクトリ。
        docs_dir (str): docs ルートディレクトリ。

    出力:
        list[dict]: 未マージドキュメント情報のリスト。
          各要素: { diff_path, master_path, phase, process, iteration, base_version }

    副作用:
        なし。
    """
    pattern = os.path.join(iter_dir, "**", "*.md")
    all_files = glob.glob(pattern, recursive=True)
    _lib.debug_log(_S, "glob", count=len(all_files), pattern=pattern)

    results = []
    for path in sorted(all_files):
        fm = _lib.parse_fm(path)
        if not fm:
            continue

        if fm.get("doc-kind") != "diff":
            continue
        if fm.get("status") != "approved":
            continue

        master_path = _resolve_master_path(path, iter_dir, docs_dir)
        if master_path is None:
            _lib.debug_log(_S, "skip-no-phase-map", path=path)
            continue

        if not _is_unmerged(fm, master_path):
            _lib.debug_log(_S, "already-merged", path=path, master=master_path)
            continue

        # iter/iter1/phase2/... → iterN のフォルダ名からイテレーション番号を抽出
        abs_iter = os.path.abspath(iter_dir)
        rel = os.path.relpath(os.path.abspath(path), abs_iter).replace("\\", "/")
        parts = rel.split("/")
        iter_num = fm.get("iteration")
        if iter_num is None:
            # フォルダ名 "iter1" からフォールバック抽出
            try:
                iter_num = int(parts[0].replace("iter", ""))
            except (ValueError, IndexError):
                iter_num = None

        phase_key = parts[1] if len(parts) > 1 else ""
        phase_dir = PHASE_MAP.get(phase_key, phase_key)
        process = _extract_process_number(os.path.basename(path))

        entry = {
            "diff_path":    os.path.normpath(path).replace("\\", "/"),
            "master_path":  os.path.normpath(master_path).replace("\\", "/"),
            "phase":        phase_dir,
            "process":      process,
            "iteration":    iter_num,
            "base_version": str(fm.get("base-version", "")),
        }
        _lib.debug_log(_S, "found-unmerged", **entry)
        results.append(entry)

    return results


def main():
    """エントリーポイント: CLI 引数を解析してスキャンを実行し JSON を出力する。

    責務:
        --iter-dir / --docs-dir を解析し scan() を呼び出す。
        結果を JSON として stdout へ出力する。

    入力:
        sys.argv: --iter-dir, --docs-dir

    出力:
        stdout: JSON { "unmerged": [...], "total": N }

    副作用:
        デバッグログ書き込み (デバッグ有効時)。
        エラー時 sys.exit(1)。
    """
    ap = argparse.ArgumentParser(
        description="Scan iter/ for approved but not-yet-merged diff documents."
    )
    ap.add_argument("--iter-dir", default="iter", help="iter root directory (default: iter)")
    ap.add_argument("--docs-dir", default="docs", help="docs root directory (default: docs)")
    args = ap.parse_args()

    _lib.debug_log(_S, "start", iter_dir=args.iter_dir, docs_dir=args.docs_dir)

    if not os.path.isdir(args.iter_dir):
        _lib.out_err(f"iter directory not found: {args.iter_dir}")

    unmerged = scan(args.iter_dir, args.docs_dir)
    result = {"unmerged": unmerged, "total": len(unmerged)}

    _lib.debug_log(_S, "done", total=result["total"])
    _lib.out_json(result)


if __name__ == "__main__":
    main()
