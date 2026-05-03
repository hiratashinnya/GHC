#!/usr/bin/env python3
"""YAML frontmatter parsing and updating.

責務:
    Markdown ファイル先頭の YAML フロントマターの解析・更新・スキャン機能と
    タグ追加・変更履歴追記などのフロントマター操作ユーティリティを提供する。

入力 / 出力:
    各関数の docstring を参照。

副作用:
    - update_fm / add_tags / append_changelog は対象ファイルを上書きする。

依存モジュール:
    - re, json, pathlib.Path (標準ライブラリ)
    - ._io (read_text, write_text, norm)
"""

import re, json
from pathlib import Path

from ._io import read_text, write_text, norm


def _scalar(raw):
    """YAML スカラー定義文字列を Python 定義型に変換する。

    責務:
        YAML の定義値文字列を Python の小数点型・整数型・ブール型・
        文字列型に変換する。パース不能の場合は None を返す。

    入力:
        raw (str): YAML 値の生文字列。

    出力:
        int | float | bool | str | None: 変換後の Python 値。

    副作用:
        なし。

    依存モジュール:
        なし (組み込み型のみ)。
    """
    s = raw.strip()
    if not s:
        return None
    if len(s) >= 2:
        if (s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'"):
            return s[1:-1]
    if "#" in s:
        s = s[:s.index("#")].strip()
    if not s or s in ("null", "~"):
        return None
    if s in ("true", "True", "yes"):
        return True
    if s in ("false", "False", "no"):
        return False
    for conv in (int, float):
        try:
            return conv(s)
        except ValueError:
            pass
    return s


def parse_fm(path):
    """Markdown ファイルの YAML フロントマターを辞書形式で返す。

    責務:
        ファイル内容を読み込み、--- 区切りの YAML ブロックを解析して
        key-value 辞書を返す。リスト値・ネスト dict にも対応する。

    入力:
        path (str | Path): 解析対象の Markdown ファイルパス。

    出力:
        dict | None: フロントマターの key-value 辞書。
                     ファイル不存在またはフロントマターがない場合は None。

    副作用:
        なし。

    依存モジュール:
        - re, json (標準ライブラリ)、._io.read_text。
    """
    text = read_text(path)
    if text is None:
        return None
    m = re.match(r"^---[ \t]*\r?\n(.*?)\r?\n---", text, re.DOTALL)
    if not m:
        return None
    result = {}
    lines = m.group(1).split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if not s or s.startswith("#"):
            i += 1
            continue
        if ln[0:1].isspace():
            i += 1
            continue
        if ":" not in s:
            i += 1
            continue
        ci = s.index(":")
        key = s[:ci].strip()
        rest = s[ci + 1:].strip()
        if rest.startswith("["):
            try:
                result[key] = json.loads(rest)
            except json.JSONDecodeError:
                result[key] = rest
            i += 1
        elif rest == "":
            items = []
            i += 1
            while i < len(lines) and lines[i][:1] in (" ", "\t"):
                sl = lines[i].strip()
                if sl.startswith("- "):
                    iv = sl[2:].strip()
                    if ":" in iv:
                        k2, v2 = iv.split(":", 1)
                        items.append({k2.strip(): _scalar(v2)})
                    else:
                        items.append(_scalar(iv))
                elif ":" in sl and items and isinstance(items[-1], dict):
                    k2, v2 = sl.split(":", 1)
                    items[-1][k2.strip()] = _scalar(v2)
                i += 1
            result[key] = items
        else:
            result[key] = _scalar(rest)
            i += 1
    return result


def scan_fm(directory, recursive=True):
    """.md ファイルをスキャンし、'_path' キー付きの辞書リストを返す。

    責務:
        指定ディレクトリ内の .md ファイル（dashboard.md を除く）を昇順ウォークし、
        parse_fm に成功したもののみを返すリストに 当該ファイルの _path を加えない。

    入力:
        directory (str | Path): スキャン対象ディレクトリ。
        recursive (bool)      : 再帰スキャンするかどうか (デフォルト: True)。

    出力:
        list[dict]: '_path' キーを含むフロントマター辞書のリスト。

    副作用:
        なし。

    依存モジュール:
        - pathlib.Path (標準ライブラリ)、._io.norm、parse_fm (同モジュール)。
    """
    d = Path(directory)
    if not d.exists():
        return []
    pat = "**/*.md" if recursive else "*.md"
    out = []
    for p in sorted(d.glob(pat)):
        if p.name == "dashboard.md":
            continue
        fm = parse_fm(str(p))
        if fm is not None:
            fm["_path"] = norm(p)
            out.append(fm)
    return out


def _ser(v):
    """Python 値を YAML インライン形式に直列化する。

    責務:
        Python の None / bool / str / int / float / list を
        YAML のインライン値文字列に変換する。

    入力:
        v (Any): 直列化対象の Python 値。

    出力:
        str: YAML 如れの文字列 (例: '"value"', 'true', '42', '[...]')。

    副作用:
        なし。

    依存モジュール:
        - json (標準ライブラリ)。
    """
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, str):
        return f'"{v}"'
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, list):
        return "[]" if not v else json.dumps(v, ensure_ascii=False)
    return str(v)


def update_fm(path, updates):
    """フロントマターのスカラー / インラインリストフィールドを更新する。

    責務:
        path の Markdown ファイルの --- ブロック内の指定キーを updates
        の値で上書きする。キーがなければ末尾に追加する。

    入力:
        path (str)       : 更新対象の Markdown ファイルパス。
        updates (dict)   : { キー: 新しい値 } 。

    出力:
        bool: 成功時 True、ファイル不存在またはフロントマターなしの場合 False。

    副作用:
        - path のファイルを上書きする。

    依存モジュール:
        - re (標準ライブラリ)、._io (read_text, write_text)、_ser (同モジュール)。
    """
    text = read_text(path)
    if text is None:
        return False
    m = re.match(r"^(---[ \t]*\r?\n)(.*?)(\r?\n---)", text, re.DOTALL)
    if not m:
        return False
    fm_lines = m.group(2).split("\n")
    body = text[m.end():]
    done = set()
    out = []
    skip = False
    for ln in fm_lines:
        if skip:
            if ln[:1] in (" ", "\t"):
                continue
            skip = False
        s = ln.strip()
        key = None
        if s and not ln[0:1].isspace() and ":" in s:
            key = s[:s.index(":")].strip()
        if key and key in updates:
            out.append(f"{key}: {_ser(updates[key])}")
            done.add(key)
            rest = s[s.index(":") + 1:].strip()
            if rest == "":
                skip = True
        else:
            out.append(ln)
    for k, v in updates.items():
        if k not in done:
            out.append(f"{k}: {_ser(v)}")
    new = m.group(1) + "\n".join(out) + m.group(3) + body
    write_text(path, new)
    return True


def add_tags(path, new_tags):
    """タグ配列に重複を除いてタグを追加する。

    責務:
        path のフロントマターから tags を取得し、new_tags を重複なしでマージする。

    入力:
        path (str)          : 対象の Markdown ファイルパス。
        new_tags (list[str]): 追加するタグのリスト。

    出力:
        bool: update_fm の成功フラグ。フロントマターなしの場合 False。

    副作用:
        - path の YAML フロントマターの tags 配列を変更する。

    依存モジュール:
        - parse_fm, update_fm (同モジュール)。
    """
    fm = parse_fm(path)
    if fm is None:
        return False
    cur = fm.get("tags") or []
    merged = list(cur) + [t for t in new_tags if t not in cur]
    return update_fm(path, {"tags": merged})


def append_changelog(path, date_str, reason, version="", author=""):
    """変更履歴テーブルに行を追記する（セクション不在時は新規作成）。

    責務:
        path 内の "## 変更履歴" セクションに新しい行を追記する。
        セクションがなければファイル末尾にテーブルごと追加する。

    入力:
        path (str)     : 対象の Markdown ファイルパス。
        date_str (str) : 変更日付 ("YYYY-MM-DD" 形式)。
        reason (str)   : 変更内容の記述。
        version (str)  : 変更時のバージョン文字列 (デフォルト: "")。
        author (str)   : 担当者名 (デフォルト: "")。

    出力:
        bool: 成功時 True、ファイル読み込み失敗時 False。

    副作用:
        - path の変更履歴セクションを上書きまたは末尾に追記する。

    依存モジュール:
        - re (標準ライブラリ)、._io (read_text, write_text)。
    """
    text = read_text(path)
    if text is None:
        return False
    row = f"| {date_str} | {version} | {reason} | {author} |"
    m2 = re.search(r"(## 変更履歴[^\n]*\n(?:\|[^\n]*\n)*)", text)
    if m2:
        pos = m2.end()
        text = text[:pos] + row + "\n" + text[pos:]
    else:
        text = (
            text.rstrip()
            + f"\n\n## 変更履歴\n\n| 日付 | バージョン | 変更内容 | 担当者 |\n| ------ | ----------- | --------- | ------ |\n{row}\n"
        )
    write_text(path, text)
    return True
