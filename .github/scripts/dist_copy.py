#!/usr/bin/env python3
"""dist_copy.py — 配布対象ファイルを dist/ ディレクトリにコピーするモジュール。

責務: DistTarget が保持するファイル一覧をリポジトリ相対パスを保ったまま out_dir にコピーする。
     テスト関連ファイルの判定・除去はエージェントの責務であり、このモジュールでは行わない。
入力: DistTarget, out_dir, repo_root
出力: コピーされたファイルパスのリスト
副作用: ファイルシステムへの書き込み
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

from dist_models import DistTarget


def _dest_path(src: Path, out_dir: Path, repo_root: Path) -> Path:
    """コピー先のパスを返す。

    責務: repo_root からの相対パスを out_dir 以下に射影する。
    入力: src — コピー元, out_dir — 出力ルート, repo_root — リポジトリルート
    出力: コピー先パス
    副作用: なし
    """
    try:
        rel = src.relative_to(repo_root)
    except ValueError:
        rel = Path(src.name)
    return out_dir / rel


def _copy_directory(src: Path, out_dir: Path, repo_root: Path) -> List[Path]:
    """パッケージディレクトリを out_dir 以下に再帰コピーする。

    責務: ディレクトリ配下のファイルをすべてコピーし、コピー先パスを返す。
    入力: src — ソースディレクトリ, out_dir, repo_root
    出力: コピーされたファイルパスのリスト
    副作用: ファイルシステムへの書き込み
    """
    copied: List[Path] = []
    for child in src.rglob("*"):
        if not child.is_file():
            continue
        child_dest = _dest_path(child, out_dir, repo_root)
        child_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(child, child_dest)
        copied.append(child_dest)
    return copied


def _copy_file(src: Path, dest: Path) -> None:
    """単一ファイルを dest にコピーする。

    責務: ディレクトリを作成してファイルをコピーする。
    入力: src — コピー元, dest — コピー先
    出力: なし
    副作用: ファイルシステムへの書き込み
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def copy_files_to_dist(
    target: DistTarget,
    out_dir: Path,
    repo_root: Path,
) -> List[Path]:
    """DistTarget のファイルを out_dir にコピーし、コピー先パスのリストを返す。

    責務: 全対象ファイルをリポジトリ相対パスを保ったまま out_dir にコピーする。
          ファイルの選別（テスト除外等）はエージェントが事前に行う想定。
    入力: target — DistTarget, out_dir — 出力先, repo_root
    出力: コピーされたファイルパスのリスト
    副作用: ファイルシステムへの書き込み（ディレクトリ作成・ファイルコピー）
    """
    copied: List[Path] = []
    out_dir.mkdir(parents=True, exist_ok=True)

    for src in target.all_files():
        if src.is_dir():
            copied.extend(_copy_directory(src, out_dir, repo_root))
        else:
            dest = _dest_path(src, out_dir, repo_root)
            _copy_file(src, dest)
            copied.append(dest)

    return copied
