#!/usr/bin/env python3
"""dist_readme.py — 配布パッケージの日本語 README.md を生成するモジュール。

責務: フォルダ構成・配置先・依存関係・セットアップ手順を記載した README を生成する。
入力: DistTarget, out_dir, コピー済みファイルリスト, repo_root
出力: 生成した README.md のパス
副作用: ファイルへの書き込み
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from dist_models import DistTarget


def _build_folder_tree(base: Path, prefix: str = "") -> List[str]:
    """ディレクトリツリーをテキスト表現のリストで返す（再帰）。

    責務: フォルダ構成の可視化テキストを生成する。
    入力: base — ルートディレクトリ, prefix — インデントプレフィックス
    出力: ツリー表現の行リスト
    副作用: なし
    """
    lines: List[str] = []
    entries = sorted(base.iterdir(), key=lambda p: (p.is_file(), p.name))
    for index, entry in enumerate(entries):
        is_last = index == len(entries) - 1
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{entry.name}")
        if entry.is_dir():
            extension = "    " if is_last else "│   "
            lines.extend(_build_folder_tree(entry, prefix + extension))
    return lines


def _build_placement_text(copied_files: List[Path], out_dir: Path) -> str:
    """コピーされたファイルの配置先一覧テキストを返す。

    責務: out_dir 相対パスから配置先説明を組み立てる。
    入力: copied_files, out_dir
    出力: Markdown リスト形式の文字列
    副作用: なし
    """
    lines = []
    for copied in copied_files:
        try:
            rel = copied.relative_to(out_dir)
            lines.append(f"- `{rel}` → 配置先: `./{rel}`")
        except ValueError:
            pass
    return "\n".join(lines) if lines else "（コピーファイルなし）"


def generate_readme(
    target: DistTarget,
    out_dir: Path,
    copied_files: List[Path],
    repo_root: Path,
) -> Path:
    """配布物ルートに日本語 README.md を生成する。

    責務: フォルダ構成・配置先・使用方法を記載した README を作成する。
    入力: target, out_dir, copied_files, repo_root
    出力: 生成した README.md のパス
    副作用: ファイルへの書き込み
    """
    tree_text = "\n".join(_build_folder_tree(out_dir))
    placement_text = _build_placement_text(copied_files, out_dir)
    script_name = target.name.replace("-", "_")

    entrypoint_desc = "\n".join(
        f"- `{ep.relative_to(repo_root)}`" for ep in target.entrypoint_paths
    ) or "（なし）"
    dep_desc = "\n".join(
        f"- `{dep.relative_to(repo_root)}`" for dep in target.dependency_paths
    ) or "（なし）"
    hook_json_info = (
        f"`{target.hook_json_path.relative_to(repo_root)}`"
        if target.hook_json_path
        else "（なし）"
    )

    content = f"""# {target.name} — 配布パッケージ

## 概要

このパッケージは **{target.name}** フックの配布用ファイル一式です。  
テスト関連ファイルは除去済みです。本番環境への配置に適した状態になっています。

---

## 配布物のフォルダ構成

```
{out_dir.name}/
{tree_text}
```

---

## 配置先のフォルダ構成

このパッケージは、対象リポジトリのルートを基準として以下の場所に配置します。

```
<your-repo>/
  .github/
    hooks/
      {target.name}.json          ← フック設定ファイル
      config/                     ← 設定ファイル（存在する場合）
      scripts/
        entrypoints/              ← エントリーポイント Python スクリプト
        core/                     ← コアモジュール
        shared/                   ← 共有ユーティリティ
        access_control/           ← アクセス制御モジュール（使用する場合）
        tooling/                  ← ツール入力解析モジュール（使用する場合）
```

---

## 各ファイルの配置

{placement_text}

---

## 依存関係

### エントリーポイント
{entrypoint_desc}

### 依存ファイル
{dep_desc}

### フック設定ファイル
{hook_json_info}

---

## セットアップ手順

### 1. ファイルの配置

同梱のデプロイスクリプトを使用することで、ファイルを自動的に配置できます：

```powershell
# Windows / PowerShell
.\\deploy.ps1 -TargetRepo <対象リポジトリのパス>
```

```bash
# Linux / macOS
bash deploy.sh <対象リポジトリのパス>
```

### 2. フック設定の有効化

GitHub Copilot の Hooks 設定でこのパッケージの JSON 設定ファイルを参照してください。

### 3. 動作確認

フックが正しく動作しているかを確認するには、VS Code の
`View > Output > GitHub Copilot Chat (Hooks)` を開き、ログを確認してください。

---

## デバッグ

デバッグログを有効にするには、エントリーポイントと同じディレクトリに
`.debug` ファイルを作成します：

```powershell
# Windows
New-Item -ItemType File ".github/hooks/scripts/entrypoints/{script_name}.debug"
```

ログは `.github/hooks/scripts/entrypoints/{script_name}.debug.log` に出力されます。

---

## 注意事項

- このパッケージはテスト関連ファイルを含みません
- テストが必要な場合は、元のリポジトリを参照してください
- Python 標準ライブラリのみを使用しています（追加インストール不要）
"""

    readme_path = out_dir / "README.md"
    readme_path.write_text(content, encoding="utf-8")
    return readme_path
