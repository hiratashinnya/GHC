#!/usr/bin/env python3
"""Phase and process path helpers.

責務:
    フェーズ・プロセス番号から docs/ 類のパスを計算するユーティリティ集。
    詳細設計コンポーネントディレクトリの洗い出し・変更ファイル分類機能も提供する。

入力 / 出力:
    各関数の docstring を参照。

副作用:
    なし (全関数純粋関数)。

依存モジュール:
    - os, pathlib.Path (標準ライブラリ)
    - ._config (DD_OVERVIEW, PROC_FILE, PHASES)
    - ._io (norm)
"""

import os
from pathlib import Path

from ._config import DD_OVERVIEW, PROC_FILE, PHASES
from ._io import norm


def phase_path(phase, docs="docs"):
    """フェーズディレクトリへの正規化パスを返す。

    責務:
        docs/<phase> を os.path.join で結合し、norm でフォワードスラッシュに変換する。

    入力:
        phase (str) : フェーズ名 ("requirements" など)。
        docs (str)  : docs ルートディレクトリ (デフォルト: "docs")。

    出力:
        str: フォワードスラッシュ形式のディレクトリパス。

    副作用:
        なし。

    依存モジュール:
        - os (標準ライブラリ)、._io.norm。
    """
    return norm(os.path.join(docs, phase))


def proc_filepath(phase, proc_num, docs="docs"):
    """プロセスドキュメントの docs 相対パスを返す。

    責務:
        フェーズとプロセス番号から対応するファイル名を PROC_FILE / DD_OVERVIEW
        マッピングから取得し、docs/<phase>/<filename> パスを返す。

    入力:
        phase (str)    : フェーズ名。
        proc_num (int) : プロセス番号 (1–5)。
        docs (str)     : docs ルートディレクトリ (デフォルト: "docs")。

    出力:
        str: フォワードスラッシュ形式のファイルパス。
             proc_num がマッピングに存在しない場合は空文字列を含むパス。

    副作用:
        なし。

    依存モジュール:
        - os (標準ライブラリ)、._config (DD_OVERVIEW, PROC_FILE)、._io.norm。
    """
    fmap = DD_OVERVIEW if phase == "detailed-design" else PROC_FILE
    return norm(os.path.join(docs, phase, fmap.get(proc_num, "")))


def list_dd_components(docs="docs"):
    """detailed-design/components/ 配下のコンポーネント .md ファイルのリストを返す。

    責務:
        docs/detailed-design/components/ を再帰スキャンし、
        見つかった全 .md ファイルパスを昇順ソートして返す。

    入力:
        docs (str): docs ルートディレクトリ (デフォルト: "docs")。

    出力:
        list[str]: 正規化パスのリスト。
                   ディレクトリが存在しない場合は空リスト。

    副作用:
        なし。

    依存モジュール:
        - pathlib.Path (標準ライブラリ)、._io.norm。
    """
    cdir = Path(docs) / "detailed-design" / "components"
    if not cdir.exists():
        return []
    return sorted(norm(p) for p in cdir.rglob("*.md"))


def list_dd_comp_ids(docs="docs"):
    """detailed-design/components/ 配下のコンポーネントディレクトリ名リストを返す。

    責務:
        docs/detailed-design/components/ の直下ディレクトリ名を昇順ソートして返す。

    入力:
        docs (str): docs ルートディレクトリ (デフォルト: "docs")。

    出力:
        list[str]: コンポーネントディレクトリ名のリスト (ID 文字列)。
                   ディレクトリが存在しない場合は空リスト。

    副作用:
        なし。

    依存モジュール:
        - pathlib.Path (標準ライブラリ)。
    """
    cdir = Path(docs) / "detailed-design" / "components"
    if not cdir.is_dir():
        return []
    return sorted(d.name for d in cdir.iterdir() if d.is_dir())


def classify_changed_file(changed_file, docs="docs"):
    """変更ファイルのパスを解析してフェーズ情報とコンポーネントIDを返す。

    入力:
        changed_file (str) : 変更ファイルパス (絶対・相対どちらも可)。
        docs (str)         : docs ルートディレクトリ (デフォルト: "docs")。

    出力:
        dict | None: {
            "phase":     str,        フェーズ名
            "phase_idx": int,        1-based フェーズ番号
            "comp_id":   str | None, コンポーネントID (detailed-design/components/ 配下のみ)
        }
        docs/ 配下でない場合は None。

    副作用:
        なし。
    """
    try:
        rel = Path(changed_file).resolve().relative_to(Path(docs).resolve())
    except ValueError:
        return None

    parts = rel.parts
    if not parts:
        return None

    phase = parts[0]
    if phase not in PHASES:
        return None

    phase_idx = PHASES.index(phase) + 1

    comp_id = None
    if phase == "detailed-design" and len(parts) >= 3 and parts[1] == "components":
        comp_id = parts[2]

    return {"phase": phase, "phase_idx": phase_idx, "comp_id": comp_id}
