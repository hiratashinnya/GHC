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


def _target_label(target_type: str) -> str:
    """対象種別の日本語ラベルを返す。"""
    labels = {"hook": "フック", "agent": "エージェント", "skill": "スキル"}
    return labels.get(target_type, "カスタマイズ")


def _target_root_hint(target_type: str, target_name: str) -> str:
    """対象種別ごとの配置先ルートの説明を返す。"""
    if target_type == "hook":
        return f"`./.github/hooks/{target_name}.json` および `./.github/hooks/scripts/...`"
    if target_type == "agent":
        return f"`./.github/agents/{target_name}.agent.md`"
    if target_type == "skill":
        return f"`./.github/skills/{target_name}/`"
    return "`./.github/` 配下の対応パス"


def _build_debug_section(target: DistTarget, repo_root: Path) -> str:
    """エントリーポイントベースのデバッグ有効化手順を返す。"""
    debug_targets = []
    for entrypoint in target.entrypoint_paths:
        if entrypoint.is_dir() or entrypoint.suffix != ".py":
            continue
        flag_path = entrypoint.with_suffix(".debug")
        log_path = entrypoint.with_suffix(".debug.log")
        try:
            flag_rel = flag_path.relative_to(repo_root)
            log_rel = log_path.relative_to(repo_root)
        except ValueError:
            flag_rel = flag_path
            log_rel = log_path
        debug_targets.append(
            f"- フラグ: `{flag_rel}` / ログ: `{log_rel}`"
        )

    if not debug_targets:
        return "この対象には Python エントリーポイントがないため、`.debug` ファイルでの有効化手順はありません。"

    return (
        "デバッグログを有効にするには、以下の `.debug` ファイルを作成してください：\n\n"
        + "\n".join(debug_targets)
    )


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
    readme_path = out_dir / "README.md"
    # README.md が自身の配布物ツリーに表示されるよう事前に作成しておく
    readme_path.touch(exist_ok=True)
    tree_text = "\n".join(_build_folder_tree(out_dir))
    placement_text = _build_placement_text(copied_files, out_dir)
    target_label = _target_label(target.target_type)
    root_hint = _target_root_hint(target.target_type, target.name)
    debug_section = _build_debug_section(target, repo_root)

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
    config_section_title = "フック設定ファイル" if target.target_type == "hook" else "設定ファイル"
    activation_title = "フック設定の有効化" if target.target_type == "hook" else "カスタマイズ設定の有効化"
    activation_body = (
        "GitHub Copilot の Hooks 設定でこのパッケージの JSON 設定ファイルを参照してください。"
        if target.target_type == "hook"
        else "GitHub Copilot の設定で、配布したエージェント/スキルが認識されることを確認してください。"
    )
    verification_body = (
        "フックが正しく動作しているかを確認するには、VS Code の\n"
        "`View > Output > GitHub Copilot Chat (Hooks)` を開き、ログを確認してください。"
        if target.target_type == "hook"
        else "対象のエージェント/スキルを呼び出し、期待どおりに起動・参照されることを確認してください。"
    )

    content = f"""# {target.name} — 配布パッケージ

## 概要

このパッケージは **{target.name}**（{target_label}）の配布用ファイル一式です。  
テスト関連ファイルの除去は運用ポリシーに応じて実施してください（このスクリプトでは自動除去しません）。

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
  ...（配布物内の相対パスを維持して配置）
```

主な配置先: {root_hint}

---

## 各ファイルの配置

{placement_text}

---

## 依存関係

### エントリーポイント
{entrypoint_desc}

### 依存ファイル
{dep_desc}

### {config_section_title}
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

### 2. {activation_title}

{activation_body}

### 3. 動作確認

{verification_body}

---

## デバッグ

{debug_section}

---

## 注意事項

- テスト関連ファイルを含めるかどうかは配布ポリシーに合わせて判断してください
- Python 標準ライブラリのみを使用しています（追加インストール不要）
"""

    readme_path.write_text(content, encoding="utf-8")
    return readme_path
