#!/usr/bin/env python3
"""Targeted (single-file) dashboard update helpers.

責務:
    AI が 1 ファイルを書き込んだ際に、対応するダッシュボード行のみを
    更新するための純粋ビルダーを提供する。全走査を避け最小限の
    ファイル読み込みで済む。

入力 / 出力:
    各関数の docstring を参照。

副作用:
    なし (全関数純粋関数)。

依存モジュール:
    - os, re (標準ライブラリ)
    - ._config (PHASE_LABEL, PROC_FILE, DD_OVERVIEW, DD_VALIDATION, NOT_STARTED)
    - ._frontmatter (parse_fm)
    - ._io (norm)
    - ._dashboard (_resolve_status_emoji)
"""

import os
import re

from ._config import PHASE_LABEL, PROC_FILE, DD_OVERVIEW, DD_VALIDATION, NOT_STARTED
from ._frontmatter import parse_fm
from ._io import norm
from ._dashboard import _resolve_status_emoji


def build_phase_row(phase, phase_idx, docs="docs"):
    """指定フェーズの 1 行のみを返す。

    入力:
        phase (str)     : フェーズ名 ("requirements" など)。
        phase_idx (int) : テーブルに表示する 1-based フェーズ番号。
        docs (str)      : docs ルートディレクトリ (デフォルト: "docs")。

    出力:
        str: テーブル行文字列 ("| フェーズN: ... | ... |")。
    """
    pp = os.path.join(docs, phase)
    fmap = DD_OVERVIEW if phase == "detailed-design" else PROC_FILE
    cols = {str(p): _resolve_status_emoji(os.path.join(pp, fmap[p])) for p in range(1, 6)}
    cols["2v"] = (
        _resolve_status_emoji(os.path.join(pp, DD_VALIDATION))
        if phase == "detailed-design"
        else NOT_STARTED
    )
    label = f"フェーズ{phase_idx}: {PHASE_LABEL.get(phase, phase)}"
    return (
        f"| {label} | {cols['1']} | {cols['2']} | {cols['2v']}"
        f" | {cols['3']} | {cols['4']} | {cols['5']} |"
    )


def build_component_row(cid, docs="docs"):
    """指定コンポーネントの 1 行のみを返す。

    入力:
        cid (str)  : コンポーネント ID。
        docs (str) : docs ルートディレクトリ (デフォルト: "docs")。

    出力:
        str: テーブル行文字列 ("| {cid} | ... |")。
    """
    cd = os.path.join(docs, "detailed-design", "components", cid)
    e = lambda fn: _resolve_status_emoji(os.path.join(cd, fn))
    return (
        f"| {cid}"
        f" | {e(f'02-breakdown-{cid}.md')}"
        f" | {e(f'03-decisions-{cid}.md')}"
        f" | {e(f'04-artifact-{cid}.md')}"
        f" | {e(f'04-artifact-{cid}-api.md')}"
        f" | {e(f'04-artifact-{cid}-schema.md')}"
        f" | {e(f'04-artifact-{cid}-domain.md')}"
        f" | {e(f'04-artifact-{cid}-testcase.md')}"
        f" | {e(f'05-verification-{cid}.md')}"
        f" |"
    )


def _bottleneck_line_for(fp, fm):
    """フロントマター辞書からボトルネック行文字列を生成する。

    責務:
        fmのstatus / approval-required を評価し、ボトルネック該当時は箇条文字列を返す。非該当時は None。

    入力:
        fp (str)  : ファイルパス文字列 (表示用)。
        fm (dict) : フロントマター辞書。

    出力:
        str | None: ボトルネック行文字列。非該当時は None。
    """
    st = fm.get("status", "")
    ar = fm.get("approval-required", False)
    if st == "rejected":
        return f"- `{fp}`: {st}（却下）"
    if st == "under-revision":
        return f"- `{fp}`: {st}（差し戻し影響）"
    if ar and st != "approved":
        return f"- `{fp}`: {st}（承認待ち）"
    return None


def patch_bottleneck_line(dashboard_text, changed_file, docs="docs"):
    """ボトルネックセクション内の changed_file の行だけを更新する。

    責務:
        1 ファイルの parse_fm のみ実行して新しいボトルネック行を決定し、
        ダッシュボードテキストのボトルネックセクションで
        changed_file に対応する既存行を 更新 / 追加 / 削除 する。
        ボトルネックセクションが「- なし」だけの場合も正しく処理する。

    入力:
        dashboard_text (str) : dashboard.md の全テキスト。
        changed_file (str)   : AI が書き込んだファイルパス。
        docs (str)           : docs ルートディレクトリ (デフォルト: "docs")。

    出力:
        str: 更新後の dashboard.md 全テキスト。ボトルネックセクションが
             なければ元のテキストをそのまま返す。
    """
    rel = norm(changed_file)
    if not rel.startswith(norm(docs) + "/"):
        rel = norm(os.path.join(docs, changed_file)) if not os.path.isabs(changed_file) else rel

    fm = parse_fm(changed_file)
    new_line = _bottleneck_line_for(rel, fm) if fm else None

    sec_pat = re.compile(
        r"(## ボトルネック[^\n]*\n)(.*?)(?=\n## |\Z)",
        re.DOTALL,
    )
    m = sec_pat.search(dashboard_text)
    if not m:
        return dashboard_text

    body = m.group(2)
    escaped = re.escape(rel)
    existing_pat = re.compile(rf"^- `{escaped}`:.*$", re.MULTILINE)
    existing_match = existing_pat.search(body)

    if existing_match:
        if new_line:
            body = existing_pat.sub(new_line, body)
        else:
            body = existing_pat.sub("", body)
            body = re.sub(r"\n{2,}", "\n", body).strip()
            if not body or re.fullmatch(r"[\s\n]*", body):
                body = "- なし"
    else:
        if new_line:
            if body.strip() == "- なし":
                body = new_line
            else:
                body = body.rstrip("\n") + "\n" + new_line

    return dashboard_text[: m.start(2)] + body.rstrip("\n") + "\n" + dashboard_text[m.end(2):]
