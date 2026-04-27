"""Dashboard status matrix and bottleneck builders.

責務:
    docs/ 配下のドキュメントステータスからダッシュボード表示用の
    Markdown テーブル文字列とボトルネック箇条リストを構築する。

入力 / 出力:
    各関数の docstring を参照。

副作用:
    なし (全関数純粋関数)。

依存モジュール:
    - os (標準ライブラリ)
    - ._config (PHASES, PHASE_LABEL, PROC_FILE, DD_OVERVIEW, DD_VALIDATION, STATUS_EMOJI, NOT_STARTED)
    - ._frontmatter (parse_fm, scan_fm)
    - ._paths (list_dd_comp_ids)
"""

import os

from ._config import (
    PHASES, PHASE_LABEL, PROC_FILE, DD_OVERVIEW, DD_VALIDATION,
    STATUS_EMOJI, NOT_STARTED,
)
from ._frontmatter import parse_fm, scan_fm
from ._paths import list_dd_comp_ids


def _resolve_status_emoji(filepath):
    """ドキュメントのステータス絵文字を返す。ファイル不在時は NOT_STARTED を返す。

    責務:
        filepath の存在を確認し、YAML フロントマターの status 値をエモージに変換する。

    入力:
        filepath (str): ステータスを取得する Markdown ファイルパス。

    出力:
        str: STATUS_EMOJI 対応の絵文字、または NOT_STARTED (「―」)。

    副作用:
        なし。

    依存モジュール:
        - os (標準ライブラリ)、._frontmatter.parse_fm、._config (STATUS_EMOJI, NOT_STARTED)。
    """
    if not os.path.exists(filepath):
        return NOT_STARTED
    fm = parse_fm(filepath)
    if not fm:
        return NOT_STARTED
    return STATUS_EMOJI.get(fm.get("status", ""), NOT_STARTED)


def build_status_matrix_md(docs="docs"):
    """ステータスマトリクス Markdown テーブル文字列を生成する。

    責務:
        PHASESリストを巡回して各プロセスファイルのステータスを取得し、
        ダッシュボード 「フェーズ×プロセス」 Markdown テーブル文字列を返す。

    入力:
        docs (str): docs ルートディレクトリ (デフォルト: "docs")。

    出力:
        str: Markdown テーブル文字列 (ヘッダー・セパレーター・行を改行で結合)。

    副作用:
        なし。

    依存モジュール:
        - os (標準ライブラリ)、._config (PHASES, PHASE_LABEL, PROC_FILE, DD_OVERVIEW, DD_VALIDATION, NOT_STARTED)、
          _resolve_status_emoji (同モジュール)。
    """
    hdr = "| フェーズ | ① 検証 | ② 分解 | ②v 分解検証 | ③ 意思決定 | ④ 成果物 | ⑤ 検証承認 |"
    sep = "| ---------- | --- | --- | ----- | --- | --- | --- |"
    rows = [hdr, sep]
    for idx, phase in enumerate(PHASES, start=1):
        pp = os.path.join(docs, phase)
        fmap = DD_OVERVIEW if phase == "detailed-design" else PROC_FILE
        cols: dict[str, str] = {str(p): _resolve_status_emoji(os.path.join(pp, fmap[p])) for p in range(1, 6)}
        cols["2v"] = (
            _resolve_status_emoji(os.path.join(pp, DD_VALIDATION))
            if phase == "detailed-design"
            else NOT_STARTED
        )
        label = f"フェーズ{idx}: {PHASE_LABEL.get(phase, phase)}"
        rows.append(
            f"| {label} | {cols['1']} | {cols['2']} | {cols['2v']}"
            f" | {cols['3']} | {cols['4']} | {cols['5']} |"
        )
    return "\n".join(rows)


def build_component_table_md(docs="docs"):
    """詳細設計コンポーネント進捗テーブル文字列を返す。コンポーネントなし時は None。

    責務:
        detailed-design/components/ 配下の各コンポーネントディレクトリを巡回し、
        各成果物ファイルのステータスをエモージで表す Markdown テーブルを返す。

    入力:
        docs (str): docs ルートディレクトリ (デフォルト: "docs")。

    出力:
        str | None: Markdown テーブル文字列。コンポーネントがなければ None。

    副作用:
        なし。

    依存モジュール:
        - os (標準ライブラリ)、._paths.list_dd_comp_ids、_resolve_status_emoji (同モジュール)。
    """
    comp_ids = list_dd_comp_ids(docs)
    if not comp_ids:
        return None
    dd = os.path.join(docs, "detailed-design", "components")
    hdr = "| コンポーネントID | ②分解 | ③決定 | ④サマリ | ④API | ④Schema | ④Domain | ④TestCase | ⑤検証 |"
    sep = "| ------------- | ------ | ------ | --------- | ------ | --------- | --------- | ----------- | ------ |"
    rows = [hdr, sep]
    for cid in comp_ids:
        cd = os.path.join(dd, cid)
        e = lambda fn, _cd=cd: _resolve_status_emoji(os.path.join(_cd, fn))
        rows.append(
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
    return "\n".join(rows)


def find_bottleneck_lines(docs="docs"):
    """ボトルネック Markdown 箇条文字列のリストを返す。

    責務:
        docs/ 内の全ドキュメントをスキャンし、status が rejected / under-revision または
        approval-required で未承認のドキュメントを箇条字列として返す。

    入力:
        docs (str): docs ルートディレクトリ (デフォルト: "docs")。

    出力:
        list[str]: Markdown 形式の箇条文字列のリスト。
                   ボトルネックなし時は空リスト。

    副作用:
        なし。

    依存モジュール:
        - ._frontmatter.scan_fm。
    """
    items = []
    for fm in scan_fm(docs):
        st = fm.get("status", "")
        fp = fm.get("_path", "")
        ar = fm.get("approval-required", False)
        if st == "rejected":
            items.append(f"- `{fp}`: {st}（却下）")
        elif st == "under-revision":
            items.append(f"- `{fp}`: {st}（差し戻し影響）")
        elif ar and st != "approved":
            items.append(f"- `{fp}`: {st}（承認待ち）")
    return items


# ---------------------------------------------------------------------------
# Targeted (single-file) update helpers
# ---------------------------------------------------------------------------

def build_phase_row(phase, phase_idx, docs="docs"):
    """指定フェーズの 1 行のみを返す。

    責務:
        phase に対応する最大 6 ファイルだけを読み込み、
        ステータスマトリクステーブルの 1 行文字列を返す。

    入力:
        phase (str)     : フェーズ名 ("requirements" など)。
        phase_idx (int) : テーブルに表示する 1-based フェーズ番号。
        docs (str)      : docs ルートディレクトリ (デフォルト: "docs")。

    出力:
        str: テーブル行文字列 ("| フェーズN: ... | ... |")。

    副作用:
        なし。

    依存モジュール:
        - os (標準ライブラリ)、._config (PHASE_LABEL, PROC_FILE, DD_OVERVIEW,
          DD_VALIDATION, NOT_STARTED)、_resolve_status_emoji (同モジュール)。
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

    責務:
        cid に対応する 8 ファイルだけを読み込み、
        コンポーネント進捗テーブルの 1 行文字列を返す。

    入力:
        cid (str)  : コンポーネント ID。
        docs (str) : docs ルートディレクトリ (デフォルト: "docs")。

    出力:
        str: テーブル行文字列 ("| {cid} | ... |")。

    副作用:
        なし。

    依存モジュール:
        - os (標準ライブラリ)、_resolve_status_emoji (同モジュール)。
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
        fm の status / approval-required を評価し、
        ボトルネック該当時は箇条文字列を返す。非該当時は None。

    入力:
        fp (str)   : ファイルパス文字列 (表示用)。
        fm (dict)  : フロントマター辞書。

    出力:
        str | None: ボトルネック行文字列、または None。

    副作用:
        なし。

    依存モジュール:
        なし。
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
        str: 更新後の dashboard.md 全テキスト。

    副作用:
        なし (純粋関数)。

    依存モジュール:
        - re (標準ライブラリ)、._frontmatter.parse_fm、._io.norm、
          _bottleneck_line_for (同モジュール)。
    """
    import re
    from ._io import norm

    rel = norm(changed_file)
    # docs/ プレフィックスを付けずにパスが渡される場合も吸収する
    if not rel.startswith(norm(docs) + "/"):
        rel = norm(os.path.join(docs, changed_file)) if not os.path.isabs(changed_file) else rel

    fm = parse_fm(changed_file)
    new_line = _bottleneck_line_for(rel, fm) if fm else None

    # ボトルネックセクションを特定
    sec_pat = re.compile(
        r"(## ボトルネック[^\n]*\n)(.*?)(?=\n## |\Z)",
        re.DOTALL,
    )
    m = sec_pat.search(dashboard_text)
    if not m:
        return dashboard_text

    body = m.group(2)

    # 既存の changed_file 行を探す（パスが backtick で囲まれている）
    escaped = re.escape(rel)
    existing_pat = re.compile(rf"^- `{escaped}`:.*$", re.MULTILINE)
    existing_match = existing_pat.search(body)

    if existing_match:
        if new_line:
            # 更新
            body = existing_pat.sub(new_line, body)
        else:
            # 削除（その行と改行を除去）
            body = existing_pat.sub("", body)
            body = re.sub(r"\n{2,}", "\n", body).strip()
            if not body or re.fullmatch(r"[\s\n]*", body):
                body = "- なし"
    else:
        if new_line:
            # 追加（「- なし」エントリを置き換えるか末尾に追記）
            if body.strip() == "- なし":
                body = new_line
            else:
                body = body.rstrip("\n") + "\n" + new_line

    return dashboard_text[: m.start(2)] + body.rstrip("\n") + "\n" + dashboard_text[m.end(2):]
