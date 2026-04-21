#!/usr/bin/env python3
"""D-3: patch-dashboard — Rebuild and patch docs/dashboard.md in-place.

Usage:
  python patch_dashboard.py [--docs-dir docs] [--dashboard docs/dashboard.md]

Internally runs the same logic as D-1 and D-2, then replaces matching
sections in the dashboard file and updates the last-updated timestamp.

Output: JSON  { success, dashboard, updated_at }
"""
import sys, os, re, argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib

_S = "D-3:patch-dashboard"


def _replace_section(text, heading_re, new_body):
    """Replace content between a ## heading and the next ## (or EOF)."""
    pat = re.compile(
        r"(## " + heading_re + r"[^\n]*\n)(.*?)(?=\n## |\Z)",
        re.DOTALL,
    )
    m = pat.search(text)
    if m:
        return text[: m.start(2)] + new_body + "\n" + text[m.end(2):]
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs-dir", default="docs")
    ap.add_argument("--dashboard", default="docs/dashboard.md")
    args = ap.parse_args()

    _lib.debug_log(_S, "start", docs=args.docs_dir, dashboard=args.dashboard)

    text = _lib.read_text(args.dashboard)
    if text is None:
        _lib.out_err(f"Cannot read {args.dashboard}")

    matrix_md = _lib.build_matrix_md(args.docs_dir)
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
