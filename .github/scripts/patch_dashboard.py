#!/usr/bin/env python3
"""D-3: patch-dashboard — docs/dashboard.md をインプレースで再構築

責務:
    D-1 / D-2 スクリプトと同じロジックを内部実行し、ダッシュボードの
    ステータスマトリクス・コンポーネント進捗・ボトルネック各セクションを
    更新し last-updated タイムスタンプも上書きする。

入力:
    CLI 引数:
      --docs-dir      <path>  docs ルートディレクトリ (デフォルト: docs)
      --dashboard     <path>  更新対象ダッシュボードファイル (デフォルト: docs/dashboard.md)
      --changed-file  <path>  AI が書き込んだファイルパス (省略時は全体 rebuild)

出力:
    JSON (stdout):
      { success, dashboard, updated_at }

副作用:
    - docs/dashboard.md の対象セクションを上書きする。
    - last-updated フィールドを現在日時で更新する。
    - patch_dashboard.debug ファイルが存在する場合、
      patch_dashboard.debug.log にログを追記する。
    - エラー時は { success: false, error } を stdout へ出力後 sys.exit(1)。

依存モジュール:
    - _lib (debug_log, read_text, write_text, build_status_matrix_md, build_component_table_md,
            find_bottleneck_lines, build_phase_row, build_component_row, patch_bottleneck_line,
            out_err, out_json)
    - sys, os, re, argparse, datetime.datetime
"""
import sys, os, re, argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib

_S = "D-3:patch-dashboard"


def _classify_changed_file(changed_file, docs):
    """変更ファイルのパスを解析してフェーズ情報とコンポーネントIDを返す。

    責務:
        changed_file が docs/ 配下のどのフェーズ・コンポーネントに属するかを
        パス文字列のみで判定し辞書で返す。ファイルシステムアクセスは行わない。

    入力:
        changed_file (str) : 変更ファイルパス (絶対・相対どちらも可)。
        docs (str)         : docs ルートディレクトリ。

    出力:
        dict | None: {
            "phase":     str,        フェーズ名
            "phase_idx": int,        1-based フェーズ番号
            "comp_id":   str | None, コンポーネントID (detailed-design/components/ 配下のみ)
        }
        docs/ 配下でない .md ではない場合は None。

    副作用:
        なし。

    依存モジュール:
        - os, pathlib.Path (標準ライブラリ)、_lib.PHASES (定数)。
    """
    from pathlib import Path
    try:
        rel = Path(changed_file).resolve().relative_to(Path(docs).resolve())
    except ValueError:
        # docs/ 外のファイル
        return None

    parts = rel.parts
    if not parts or not parts[0]:
        return None

    phase = parts[0]
    if phase not in _lib.PHASES:
        return None

    phase_idx = _lib.PHASES.index(phase) + 1

    # detailed-design/components/<cid>/ 配下か判定
    comp_id = None
    if (
        phase == "detailed-design"
        and len(parts) >= 3
        and parts[1] == "components"
    ):
        comp_id = parts[2]

    return {"phase": phase, "phase_idx": phase_idx, "comp_id": comp_id}


def _replace_table_row(text, row_prefix_re, new_row):
    """テーブル内の特定行のみを置換する。

    責務:
        row_prefix_re にマッチするテーブル行を new_row で置換する。
        マッチしない場合は text をそのまま返す。

    入力:
        text (str)          : ダッシュボード全テキスト。
        row_prefix_re (str) : 行冒頭部分にマッチさせる正規表現パターン。
        new_row (str)       : 置換後の行文字列 (改行なし)。

    出力:
        str: 置換後のテキスト。

    副作用:
        なし。

    依存モジュール:
        - re (標準ライブラリ)。
    """
    return re.sub(
        r"^" + row_prefix_re + r".*$",
        new_row,
        text,
        count=1,
        flags=re.MULTILINE,
    )


def _replace_section(text, heading_re, new_body):
    """## 見出しから次の ## または EOF までの内容を置換する。

    責務:
        heading_re にマッチする ## 見出しブロックの本文部分を
        new_body で置換する。マッチしない場合は元の text をそのまま返す。

    入力:
        text (str)       : 置換対象の Markdown 全体文字列。
        heading_re (str) : ## タイトルにマッチさせる正規表現パターン。
        new_body (str)   : 見出し次のセクションに嵌め込む新しい本文。

    出力:
        str: 置換後の Markdown 全体文字列。

    副作用:
        なし。

    依存モジュール:
        - re (標準ライブラリ)。
    """
    pat = re.compile(
        r"(## " + heading_re + r"[^\n]*\n)(.*?)(?=\n## |\Z)",
        re.DOTALL,
    )
    m = pat.search(text)
    if m:
        return text[: m.start(2)] + new_body + "\n" + text[m.end(2):]
    return text


def main():
    """ダッシュボードファイルの各セクションを再構築しインプレースで更新する。

    責務:
        --changed-file 指定時は対象フェーズ行 / コンポーネント行 / ボトルネック行のみを
        更新する targeted モードで動作する。
        --changed-file 省略時は従来通り全体 rebuild を行う。

    入力:
        sys.argv:
          --docs-dir      <path>  docs ルートディレクトリ
          --dashboard     <path>  更新対象のダッシュボードファイル
          --changed-file  <path>  AI が書き込んだファイルパス (省略可)

    出力:
        stdout へ JSON を印字:
          { success, dashboard, updated_at }

    副作用:
        - docs/dashboard.md のステータスマトリクス・コンポーネント進捗・ボトルネック・
          last-updated セクションを上書きする。
        - _lib.debug_log によりデバッグログを書き込む場合がある。
        - エラー時 _lib.out_err を通じて sys.exit(1) で終了する。

    依存モジュール:
        - _lib (debug_log, read_text, write_text, build_status_matrix_md, build_component_table_md,
                find_bottleneck_lines, build_phase_row, build_component_row, patch_bottleneck_line,
                out_err, out_json)
        - re, argparse, datetime.datetime
    """
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
        info = _classify_changed_file(args.changed_file, args.docs_dir)
        _lib.debug_log(_S, "targeted", info=str(info))

        if info is None:
            # docs/ 外のファイル → 何もしない
            _lib.debug_log(_S, "skip", reason="not under docs/")
            _lib.out_json({"success": True, "dashboard": args.dashboard, "updated_at": now, "skipped": True})
            return

        # 1. ステータスマトリクスの対応行を更新
        phase_label_prefix = re.escape(
            f"| フェーズ{info['phase_idx']}: {_lib.PHASE_LABEL.get(info['phase'], info['phase'])}"
        )
        new_phase_row = _lib.build_phase_row(info["phase"], info["phase_idx"], args.docs_dir)
        text = _replace_table_row(text, phase_label_prefix, new_phase_row)

        # 2. コンポーネント行を更新 (detailed-design/components/ 配下の場合のみ)
        if info["comp_id"]:
            cid_prefix = re.escape(f"| {info['comp_id']}")
            new_comp_row = _lib.build_component_row(info["comp_id"], args.docs_dir)
            text = _replace_table_row(text, cid_prefix, new_comp_row)

        # 3. ボトルネック行を 1 ファイル分のみ更新
        text = _lib.patch_bottleneck_line(text, args.changed_file, args.docs_dir)

    else:
        # 全体 rebuild (従来モード)
        matrix_md = _lib.build_status_matrix_md(args.docs_dir)
        comp_md = _lib.build_component_table_md(args.docs_dir)

        bn_lines = _lib.find_bottleneck_lines(args.docs_dir)
        bn_md = "\n".join(bn_lines) if bn_lines else "- なし"

        legend = (
            "\n> ②v列 は詳細設計フェーズのみ有効。他フェーズは ─ 固定。\n\n"
            "凡例: ✅ approved / ⏳ awaiting-approval / 📝 draft"
            " / ❌ rejected / 🔙 under-revision / ─ not-started\n"
        )

        text = _replace_section(
            text,
            r"フェーズ.*プロセス.*ステータスマトリクス",
            f"\n{matrix_md}\n{legend}",
        )

        if comp_md:
            text = _replace_section(
                text,
                r"詳細設計.*コンポーネント.*進捗",
                f"\n{comp_md}\n",
            )

        text = _replace_section(text, r"ボトルネック", f"\n{bn_md}\n")

    text = re.sub(
        r'(last-updated:\s*)"[^"]*"',
        rf'\1"{now}"',
        text,
    )

    _lib.write_text(args.dashboard, text)
    _lib.debug_log(_S, "done", dashboard=args.dashboard)
    _lib.out_json({"success": True, "dashboard": args.dashboard, "updated_at": now})


if __name__ == "__main__":
    main()
