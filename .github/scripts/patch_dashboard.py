#!/usr/bin/env python3
"""D-3: patch-dashboard — docs/dashboard.md をインプレースで再構築

責務:
    D-1 / D-2 スクリプトと同じロジックを内部実行し、ダッシュボードの
    ステータスマトリクス・コンポーネント進捗・ボトルネック各セクションを
    更新し last-updated タイムスタンプも上書きする。

入力:
    CLI 引数:
      --docs-dir   <path>  docs ルートディレクトリ (デフォルト: docs)
      --dashboard  <path>  更新対象ダッシュボードファイル (デフォルト: docs/dashboard.md)

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
            find_bottleneck_lines, out_err, out_json)
    - sys, os, re, argparse, datetime.datetime
"""
import sys, os, re, argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib

_S = "D-3:patch-dashboard"


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
        D-1 / D-2 スクリプトと同じロジックの matrix / component / bottleneck を
        生成し、dashboard.md の各セクションを置換後、last-updated を現在時刻で更新する。

    入力:
        sys.argv:
          --docs-dir  <path>  docs ルートディレクトリ
          --dashboard <path>  更新対象のダッシュボードファイル

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
                find_bottleneck_lines, out_err, out_json)
        - re, argparse, datetime.datetime
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs-dir", default="docs")
    ap.add_argument("--dashboard", default="docs/dashboard.md")
    args = ap.parse_args()

    _lib.debug_log(_S, "start", docs=args.docs_dir, dashboard=args.dashboard)

    text = _lib.read_text(args.dashboard)
    if text is None:
        _lib.out_err(f"Cannot read {args.dashboard}")

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

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
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
