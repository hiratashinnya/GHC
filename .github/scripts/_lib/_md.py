#!/usr/bin/env python3
"""Markdown text manipulation utilities.

責務:
    ダッシュボード Markdown テキストに対するセクション置換・テーブル行置換の
    純粋関数を提供する。ファイル I/O は行わない。

入力 / 出力:
    各関数の docstring を参照。

副作用:
    なし (全関数純粋関数)。

依存モジュール:
    - re (標準ライブラリ)
"""

import re


def replace_section(text, heading_re, new_body):
    """## 見出しから次の ## または EOF までの内容を置換する。

    入力:
        text (str)       : 置換対象の Markdown 全体文字列。
        heading_re (str) : ## タイトルにマッチさせる正規表現パターン。
        new_body (str)   : 見出し次のセクションに嵌め込む新しい本文。

    出力:
        str: 置換後の Markdown 全体文字列。マッチしない場合は元の text。
    """
    pat = re.compile(
        r"(## " + heading_re + r"[^\n]*\n)(.*?)(?=\n## |\Z)",
        re.DOTALL,
    )
    m = pat.search(text)
    if m:
        return text[: m.start(2)] + new_body + "\n" + text[m.end(2):]
    return text


def replace_table_row(text, row_prefix_re, new_row):
    """テーブル内の特定行のみを置換する。

    入力:
        text (str)          : ダッシュボード全テキスト。
        row_prefix_re (str) : 行冒頭部分にマッチさせる正規表現パターン。
        new_row (str)       : 置換後の行文字列 (改行なし)。

    出力:
        str: 置換後のテキスト。マッチしない場合は元の text。
    """
    return re.sub(
        r"^" + row_prefix_re + r".*$",
        new_row,
        text,
        count=1,
        flags=re.MULTILINE,
    )
