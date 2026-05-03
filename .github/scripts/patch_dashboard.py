#!/usr/bin/env python3
"""D-3: patch-dashboard — docs/dashboard.md をインプレースで再構築

責務:
    ダッシュボードのステータスマトリクス・コンポーネント進捗・ボトルネック各セクションを
    更新し last-updated タイムスタンプも上書きする。

入力:
    CLI 引数:
      --docs-dir      <path>  docs ルートディレクトリ (デフォルト: docs)
      --dashboard     <path>  更新対象ダッシュボードファイル (デフォルト: docs/dashboard.md)
      --changed-file  <path>  AI が書き込んだファイルパス (省略時は全体 rebuild)

出力:
    JSON (stdout): { success, dashboard, updated_at }

副作用:
    - docs/dashboard.md の対象セクションを上書きする。
    - last-updated フィールドを現在日時で更新する。
    - patch_dashboard.debug ファイルが存在する場合、
      patch_dashboard.debug.log にログを追記する。
    - エラー時は { success: false, error } を stdout へ出力後 sys.exit(1)。

依存モジュール:
    - _lib, sys, os, re, argparse, datetime.datetime
"""
import sys, os, re, argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib

_S = "D-3:patch-dashboard"

_LEGEND = (
    "\n> ②v列 は詳細設計フェーズのみ有効。他フェーズは ─ 固定。\n\n"
    "凡例: ✅ approved / ⏳ awaiting-approval / 📝 draft"
    " / ❌ rejected / 🔙 under-revision / ─ not-started\n"
)


def _run_full_rebuild(text, docs):
    """全フェーズ・全コンポーネントを再走査してダッシュボードを完全再構築する。

    入力:
        text (str) : dashboard.md の現在のテキスト。
        docs (str) : docs ルートディレクトリ。

    出力:
        str: 更新後のテキスト。
    """
    matrix_md = _lib.build_status_matrix_md(docs)
    comp_md = _lib.build_component_table_md(docs)

    bn_lines = _lib.find_bottleneck_lines(docs)
    bn_md = "\n".join(bn_lines) if bn_lines else "- なし"

    text = _lib.replace_section(
        text,
        r"フェーズ.*プロセス.*ステータスマトリクス",
        f"\n{matrix_md}\n{_LEGEND}",
    )
    if comp_md:
        text = _lib.replace_section(
            text, r"詳細設計.*コンポーネント.*進捗", f"\n{comp_md}\n"
        )
    return _lib.replace_section(text, r"ボトルネック", f"\n{bn_md}\n")


def _run_targeted(text, changed_file, docs):
    """変更された 1 ファイルに対応するダッシュボード行のみを更新する。

    入力:
        text (str)         : dashboard.md の現在のテキスト。
        changed_file (str) : AI が書き込んだファイルパス。
        docs (str)         : docs ルートディレクトリ。

    出力:
        (str, bool): (更新後テキスト, skipped フラグ)。
                     changed_file が docs/ 配下でなければ skipped=True。
    """
    info = _lib.classify_changed_file(changed_file, docs)
    if info is None:
        # docs/ 外のファイル → 何もしない
        return text, True # skipped=True を呼び出し元に伝える

    # 1. ステータスマトリクスの対応行を更新
    phase_prefix = re.escape(
        f"| フェーズ{info['phase_idx']}: {_lib.PHASE_LABEL.get(info['phase'], info['phase'])}"
    )
    new_phase_row = _lib.build_phase_row(info["phase"], info["phase_idx"], docs)
    text = _lib.replace_table_row(text, phase_prefix, new_phase_row)

    # 2. コンポーネント行を更新 (detailed-design/components/ 配下の場合のみ)
    if info["comp_id"]:
        text = _lib.replace_table_row(
            text,
            re.escape(f"| {info['comp_id']}"),
            _lib.build_component_row(info["comp_id"], docs),
        )

    # 3. ボトルネック行を 1 ファイル分のみ更新
    text = _lib.patch_bottleneck_line(text, changed_file, docs)
    return text, False # skipped=False を呼び出し元に伝える


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs-dir", default="docs")
    ap.add_argument("--dashboard", default="docs/dashboard.md")
    ap.add_argument("--changed-file", default=None)
    args = ap.parse_args()

    _lib.debug_log(_S, "start", docs=args.docs_dir, dashboard=args.dashboard, changed_file=args.changed_file)

    text = _lib.read_text(args.dashboard)
    if text is None:
        _lib.out_err(f"Cannot read {args.dashboard}")

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if args.changed_file:
        text, skipped = _run_targeted(text, args.changed_file, args.docs_dir)
        _lib.debug_log(_S, "targeted", skipped=skipped)
        if skipped:
            # docs/ 外のファイル → 何もしない
            _lib.out_json({"success": True, "dashboard": args.dashboard, "updated_at": now, "skipped": True})
            return
    else:
        text = _run_full_rebuild(text, args.docs_dir)

    text = re.sub(r'(last-updated:\s*)"[^"]*"', rf'\1"{now}"', text)
    _lib.write_text(args.dashboard, text)
    _lib.debug_log(_S, "done", dashboard=args.dashboard)
    _lib.out_json({"success": True, "dashboard": args.dashboard, "updated_at": now})


if __name__ == "__main__":
    main()

