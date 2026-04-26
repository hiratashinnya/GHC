#!/usr/bin/env python3
"""I-1: check-split-threshold — イテレーション分割要否チェック

責務:
    breakdown ドキュメントの REQ-F / COMP / サブシステム / 高優先 NFR 数を集計し、
    閾値超過の有無に基づいてイテレーション分割の必要性を判定する。

入力:
    CLI 引数:
      --breakdown <path>  分析対象の要件分解 Markdown ファイル
                          (デフォルト: docs/requirements/02-breakdown.md)

出力:
    JSON (stdout):
      { success, split_required, counts, thresholds, triggers }
    閾値: REQ-F > 15 / サブシステム > 2 / COMP-ID > 5 / 高優先 NFR > 3

副作用:
    - check_split_threshold.debug ファイルが存在する場合、
      check_split_threshold.debug.log にログを追記する。
    - エラー時は { success: false, error } を stdout へ出力後 sys.exit(1)。

依存モジュール:
    - _lib (debug_log, read_text, out_err, out_json)
    - sys, os, re, argparse
"""
import sys, os, re, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib

_S = "I-1:check-split-threshold"

_THRESHOLDS = {
    "req_f": 15,
    "subsystems": 2,
    "comp_ids": 5,
    "nfr_high": 3,
}


def main():
    """breakdown ドキュメントを解析してイテレーション分割の必要性を判定する。

    責務:
        引数 --breakdown のファイルを読み込み、正規表現で識別子を抽出して
        閾値と比較し、結果を JSON で stdout に出力する。

    入力:
        sys.argv:
            --breakdown <path>  要件分解 Markdown ファイルパス

    出力:
        stdout へ JSON を印字:
            { success, split_required, counts, thresholds, triggers }

    副作用:
        - _lib.debug_log によりデバッグログを書き込む場合がある。
        - エラー時 _lib.out_err を通じて sys.exit(1) で終了する。

    依存モジュール:
        - _lib (debug_log, read_text, out_err, out_json)
        - re, argparse
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--breakdown", default="docs/requirements/02-breakdown.md",
                    help="Breakdown document to analyse")
    args = ap.parse_args()

    _lib.debug_log(_S, "start", file=args.breakdown)

    text = _lib.read_text(args.breakdown)
    if text is None:
        _lib.out_err(f"Cannot read {args.breakdown}")

    req_f = set(re.findall(r"REQ-F-\d+", text))
    comp_ids = set(re.findall(r"COMP-\d+", text))
    subsystems = set(re.findall(r"(?:SUB|サブシステム)[- ]?\d+", text, re.IGNORECASE))

    nfr_high = set()
    for line in text.split("\n"):
        if re.search(r"REQ-NF", line) and re.search(r"High|Must|高", line, re.IGNORECASE):
            m = re.search(r"REQ-NF-\d+", line)
            if m:
                nfr_high.add(m.group(0))

    counts = {
        "req_f": len(req_f),
        "subsystems": max(len(subsystems), 1),
        "comp_ids": len(comp_ids),
        "nfr_high": len(nfr_high),
    }

    triggers = []
    for key, thresh in _THRESHOLDS.items():
        if counts[key] > thresh:
            triggers.append({"metric": key, "count": counts[key], "threshold": thresh})

    split_required = len(triggers) > 0
    _lib.debug_log(_S, "done", counts=counts, split=split_required)
    _lib.out_json({
        "success": True,
        "split_required": split_required,
        "counts": counts,
        "thresholds": _THRESHOLDS,
        "triggers": triggers,
    })


if __name__ == "__main__":
    main()
