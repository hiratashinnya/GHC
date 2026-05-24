#!/usr/bin/env python3
"""distribute.py — 配布用フォルダを作成し、依存ファイルをコピーするユーティリティ。

責務:
  - 対象フック（またはコンポーネント）の依存ファイルを解析する
  - dist/<name>/ 以下に必要なファイルをコピーする
  - エントリーポイント・設定ファイルに日本語 README を生成する
  - テスト関連のファイル・記述を配布物から除去する（原本は変更しない）
  - 再配置用デプロイスクリプト（.ps1 / .sh）を生成する

Usage:
  python .github/scripts/distribute.py <target> [--out-dir <path>] [--repo-root <path>]

  target : フック名（例: access-control）またはスクリプト名（例: access_control）
  --out-dir : 配布物の出力先（デフォルト: dist/）
  --repo-root : リポジトリルート（デフォルト: カレントディレクトリ）
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HOOKS_ROOT = Path(".github/hooks")
SCRIPTS_ROOT = HOOKS_ROOT / "scripts"
ENTRYPOINTS_DIR = SCRIPTS_ROOT / "entrypoints"
CONFIG_DIR = HOOKS_ROOT / "config"

# テスト関連ファイルを示すパターン（大文字小文字問わず）
TEST_FILE_PATTERNS: Tuple[str, ...] = (
    "test_*.py",
    "*_test.py",
    "testcase.md",
    "testresult.md",
    "run_tests.ps1",
)

# テスト関連のディレクトリ名（完全一致）
TEST_DIR_NAMES: Tuple[str, ...] = (
    "TestHooks",
    "tests",
    "test",
    "__pycache__",
)

# テスト関連記述を除去する Markdown セクション見出しキーワード
TEST_SECTION_KEYWORDS: Tuple[str, ...] = (
    "テスト作業",
    "テストの実施",
    "testresult",
    "testcase",
    "run_tests",
    "## テスト",
    "## Test",
)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class DistTarget:
    """配布対象の情報を保持するデータクラス。"""

    name: str
    hook_json_path: Optional[Path] = None
    entrypoint_paths: List[Path] = field(default_factory=list)
    dependency_paths: List[Path] = field(default_factory=list)
    config_paths: List[Path] = field(default_factory=list)

    def all_files(self) -> List[Path]:
        """全ファイルパスのリストを返す（重複除去済み）。"""
        result: List[Path] = []
        seen: Set[Path] = set()
        candidates = (
            ([self.hook_json_path] if self.hook_json_path else [])
            + self.entrypoint_paths
            + self.dependency_paths
            + self.config_paths
        )
        for path in candidates:
            if path not in seen:
                result.append(path)
                seen.add(path)
        return result


@dataclass
class DistResult:
    """配布処理の結果を保持するデータクラス。"""

    out_dir: Path
    copied_files: List[Path] = field(default_factory=list)
    readme_paths: List[Path] = field(default_factory=list)
    deploy_script_ps1: Optional[Path] = None
    deploy_script_sh: Optional[Path] = None
    skipped_test_files: List[Path] = field(default_factory=list)

    def summary(self) -> str:
        """処理結果のサマリー文字列を返す。"""
        lines = [
            f"配布先: {self.out_dir}",
            f"コピーされたファイル数: {len(self.copied_files)}",
            f"除外されたテストファイル数: {len(self.skipped_test_files)}",
            f"生成されたREADME: {', '.join(str(p) for p in self.readme_paths)}",
        ]
        if self.deploy_script_ps1:
            lines.append(f"デプロイスクリプト(PS1): {self.deploy_script_ps1}")
        if self.deploy_script_sh:
            lines.append(f"デプロイスクリプト(SH): {self.deploy_script_sh}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Dependency analysis
# ---------------------------------------------------------------------------

def _extract_python_imports(py_path: Path) -> Set[str]:
    """Python ファイルから import されているモジュール名のセットを返す。

    責務: AST パース + フォールバック正規表現で import 文を抽出する。
    入力: py_path — 解析対象の Python ファイルパス
    出力: モジュール名のセット（パッケージプレフィックスなし）
    副作用: なし
    """
    imports: Set[str] = set()
    try:
        source = py_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(py_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split(".")[0])
    except SyntaxError:
        # フォールバック: 正規表現
        source = py_path.read_text(encoding="utf-8")
        for match in re.finditer(r"^(?:from|import)\s+([\w.]+)", source, re.MULTILINE):
            imports.add(match.group(1).split(".")[0])
    return imports


def _find_module_file(module_name: str, search_dirs: List[Path]) -> Optional[Path]:
    """モジュール名からファイルパス（またはパッケージディレクトリ）を解決する。

    責務: search_dirs を順に探索し、最初に見つかったファイルまたはパッケージを返す。
    入力: module_name — モジュール名, search_dirs — 探索対象のディレクトリリスト
    出力: 見つかったファイルパス（またはパッケージ dir）、または None
    副作用: なし
    """
    for search_dir in search_dirs:
        # 単一ファイルモジュール
        candidate = search_dir / f"{module_name}.py"
        if candidate.exists():
            return candidate
        # パッケージディレクトリ（__init__.py の有無にかかわらず）
        pkg_dir = search_dir / module_name
        if pkg_dir.is_dir():
            return pkg_dir
    return None


def resolve_dependencies(
    entrypoint: Path,
    search_dirs: List[Path],
    visited: Optional[Set[Path]] = None,
) -> List[Path]:
    """エントリーポイントの依存ファイルを再帰的に解決する。

    責務: import グラフを深さ優先探索し、全依存ファイルを収集する。
          パッケージディレクトリ（フォルダ）はそのまま返す（中の .py を個別追跡はしない）。
    入力: entrypoint — 起点ファイルまたはパッケージ dir, search_dirs — モジュール探索ディレクトリ
    出力: 依存ファイル/ディレクトリのリスト（重複なし、トポロジカル順）
    副作用: なし
    """
    if visited is None:
        visited = set()

    if entrypoint in visited:
        return []
    visited.add(entrypoint)

    # パッケージディレクトリの場合は中身を再帰探索せず、ディレクトリ自体を返す
    if entrypoint.is_dir():
        return []

    deps: List[Path] = []
    imports = _extract_python_imports(entrypoint)

    for module_name in sorted(imports):
        module_path = _find_module_file(module_name, search_dirs)
        if module_path is None or module_path in visited:
            continue
        # 再帰的に依存を解決する（この呼び出しで module_path が visited に追加される）
        transitive = resolve_dependencies(module_path, search_dirs, visited)
        deps.extend(transitive)
        # module_path 自身は recursive call の戻り値に含まれないため明示的に追加する
        deps.append(module_path)

    return deps


def find_hook_target(target_name: str, repo_root: Path) -> DistTarget:
    """対象名からフックの DistTarget を構築する。

    責務: フック JSON・エントリーポイント・依存ファイル・設定ファイルを発見する。
    入力: target_name — フック名（例: access-control）, repo_root — リポジトリルート
    出力: DistTarget データクラス
    副作用: なし
    """
    hooks_root = repo_root / HOOKS_ROOT
    scripts_root = repo_root / SCRIPTS_ROOT
    entrypoints_dir = repo_root / ENTRYPOINTS_DIR
    config_dir = repo_root / CONFIG_DIR

    # フック JSON を探す（ハイフン名・アンダースコア名の両方を試す）
    hook_json_path: Optional[Path] = None
    for json_name in (target_name, target_name.replace("_", "-")):
        candidate = hooks_root / f"{json_name}.json"
        if candidate.exists():
            hook_json_path = candidate
            break

    # エントリーポイントを探す（スクリプト名 = target_name アンダースコア変換）
    script_name = target_name.replace("-", "_")
    entrypoint_paths: List[Path] = []
    ep_candidate = entrypoints_dir / f"{script_name}.py"
    if ep_candidate.exists():
        entrypoint_paths.append(ep_candidate)
    else:
        # glob で類似名を探す
        entrypoint_paths = list(entrypoints_dir.glob(f"*{script_name}*.py"))

    # 依存ファイルを解析する
    search_dirs = [
        scripts_root / "core",
        scripts_root / "access_control",
        scripts_root / "tooling",
        scripts_root / "shared",
        scripts_root,
        # .github/scripts 配下のパッケージ（_lib 等）も探索する
        repo_root / ".github" / "scripts",
    ]
    dependency_paths: List[Path] = []
    for ep in entrypoint_paths:
        deps = resolve_dependencies(ep, search_dirs)
        for dep in deps:
            if dep not in dependency_paths:
                dependency_paths.append(dep)

    # 設定ファイルを探す
    config_paths: List[Path] = []
    if hook_json_path:
        # JSON 内の config パスを抽出
        try:
            hook_data = json.loads(hook_json_path.read_text(encoding="utf-8"))
            for _event, commands in hook_data.get("hooks", {}).items():
                for cmd in commands:
                    command_str = cmd.get("command", "")
                    for token in command_str.split():
                        if token.endswith(".json") and "config" in token:
                            cfg_path = repo_root / token.lstrip("./")
                            if cfg_path.exists():
                                config_paths.append(cfg_path)
        except (json.JSONDecodeError, KeyError):
            pass

    # config ディレクトリから同名の設定ファイルも探す
    for cfg_name in (target_name, script_name):
        cfg_candidate = config_dir / f"{cfg_name}.json"
        if cfg_candidate.exists() and cfg_candidate not in config_paths:
            config_paths.append(cfg_candidate)

    return DistTarget(
        name=target_name,
        hook_json_path=hook_json_path,
        entrypoint_paths=entrypoint_paths,
        dependency_paths=dependency_paths,
        config_paths=config_paths,
    )


# ---------------------------------------------------------------------------
# File copy (test exclusion)
# ---------------------------------------------------------------------------

def _is_test_file(path: Path) -> bool:
    """テスト関連ファイルかどうかを判定する。

    責務: ファイル名パターンおよびパス構成要素からテストファイルを識別する。
    入力: path — 判定対象のファイルパス
    出力: テストファイルならば True
    副作用: なし
    """
    # パス構成要素にテストディレクトリ名が含まれる場合
    for part in path.parts:
        if part in TEST_DIR_NAMES:
            return True
    # ファイル名パターン
    for pattern in TEST_FILE_PATTERNS:
        if path.match(pattern):
            return True
    return False


def _strip_test_sections_from_markdown(content: str) -> str:
    """Markdown からテスト関連セクションを除去した文字列を返す。

    責務: テストセクション見出し以降の行を次の同レベル見出しまで削除する。
    入力: content — Markdown テキスト
    出力: テスト関連セクションを除去した Markdown テキスト
    副作用: なし
    """
    lines = content.splitlines(keepends=True)
    result: List[str] = []
    skip_until_heading: Optional[str] = None  # 次にこのプレフィックスが来たらスキップ終了

    for line in lines:
        if skip_until_heading is not None:
            # 同レベル以上の見出しが来たらスキップ終了
            if re.match(r"^#{1," + str(len(skip_until_heading)) + r"}\s", line):
                skip_until_heading = None
                result.append(line)
            continue

        # テスト関連セクションの開始を検出
        is_test_section = False
        for keyword in TEST_SECTION_KEYWORDS:
            if keyword.lower() in line.lower() and re.match(r"^#+\s", line):
                is_test_section = True
                # 見出しレベルを取得
                heading_level = len(re.match(r"^(#+)", line).group(1))
                skip_until_heading = "#" * heading_level
                break

        if not is_test_section:
            result.append(line)

    return "".join(result)


def copy_files_to_dist(
    target: DistTarget,
    out_dir: Path,
    repo_root: Path,
) -> Tuple[List[Path], List[Path]]:
    """ファイルを配布先ディレクトリにコピーし、テストファイルを除外する。

    責務: 全対象ファイルを dist/ 以下にコピーし、テスト関連ファイルをスキップする。
    入力: target — DistTarget, out_dir — 出力先, repo_root — リポジトリルート
    出力: (コピーされたファイルリスト, スキップされたファイルリスト)
    副作用: ファイルシステムへの書き込み（コピー）
    """
    copied: List[Path] = []
    skipped: List[Path] = []
    out_dir.mkdir(parents=True, exist_ok=True)

    for src in target.all_files():
        if _is_test_file(src):
            skipped.append(src)
            continue

        # repo_root からの相対パスを保ちながらコピー先を決める
        try:
            rel = src.relative_to(repo_root)
        except ValueError:
            rel = Path(src.name)

        dest = out_dir / rel

        # パッケージディレクトリはディレクトリごとコピー（テストファイルを除外）
        if src.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
            for child in src.rglob("*"):
                if child.is_file():
                    if _is_test_file(child):
                        skipped.append(child)
                        continue
                    try:
                        child_rel = child.relative_to(repo_root)
                    except ValueError:
                        child_rel = child.relative_to(src.parent)
                    child_dest = out_dir / child_rel
                    child_dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(child, child_dest)
                    copied.append(child_dest)
            continue

        dest.parent.mkdir(parents=True, exist_ok=True)

        # Markdown はテスト関連セクションを除去してコピー
        if src.suffix.lower() in (".md",):
            content = src.read_text(encoding="utf-8")
            cleaned = _strip_test_sections_from_markdown(content)
            dest.write_text(cleaned, encoding="utf-8")
        else:
            shutil.copy2(src, dest)

        copied.append(dest)

    return copied, skipped


# ---------------------------------------------------------------------------
# README generation
# ---------------------------------------------------------------------------

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


def generate_readme(
    target: DistTarget,
    out_dir: Path,
    copied_files: List[Path],
    repo_root: Path,
) -> Path:
    """配布物ルートに日本語 README.md を生成する。

    責務: フォルダ構成・配置先・使用方法を記載した README を作成する。
    入力: target, out_dir, copied_files, repo_root
    出力: 生成した README のパス
    副作用: ファイルへの書き込み
    """
    # 配布物フォルダ構成を生成
    tree_lines = _build_folder_tree(out_dir)
    tree_text = "\n".join(tree_lines)

    # 元のエントリーポイントのリポジトリ内パス
    entrypoint_descriptions = "\n".join(
        f"- `{ep.relative_to(repo_root)}`"
        for ep in target.entrypoint_paths
    )

    # 元の依存ファイルのリポジトリ内パス
    dep_descriptions = "\n".join(
        f"- `{dep.relative_to(repo_root)}`"
        for dep in target.dependency_paths
    )

    # 配置先フォルダ構成の説明（.github/hooks/ を基準）
    placement_lines = []
    for copied in copied_files:
        try:
            rel = copied.relative_to(out_dir)
            placement_lines.append(f"- `{rel}` → 配置先: `./{rel}`")
        except ValueError:
            pass
    placement_text = "\n".join(placement_lines) if placement_lines else "（コピーファイルなし）"

    hook_json_info = (
        f"`{target.hook_json_path.relative_to(repo_root)}`"
        if target.hook_json_path
        else "（なし）"
    )

    readme_content = f"""# {target.name} — 配布パッケージ

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
{entrypoint_descriptions if entrypoint_descriptions else "（なし）"}

### 依存ファイル
{dep_descriptions if dep_descriptions else "（なし）"}

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

VS Code の設定ファイル（`.vscode/settings.json` または `settings.json`）に以下を追加します：

```json
{{
  "github.copilot.chat.agent.thinkingTool": true
}}
```

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
New-Item -ItemType File ".github/hooks/scripts/entrypoints/{target.name.replace('-', '_')}.debug"
```

ログは `.github/hooks/scripts/entrypoints/{target.name.replace('-', '_')}.debug.log` に出力されます。

---

## 注意事項

- このパッケージはテスト関連ファイルを含みません
- テストが必要な場合は、元のリポジトリを参照してください
- Python 標準ライブラリのみを使用しています（追加インストール不要）
"""

    readme_path = out_dir / "README.md"
    readme_path.write_text(readme_content, encoding="utf-8")
    return readme_path


# ---------------------------------------------------------------------------
# Deploy script generation
# ---------------------------------------------------------------------------

def generate_deploy_scripts(target: DistTarget, out_dir: Path) -> Tuple[Path, Path]:
    """再配置用デプロイスクリプト（PowerShell / Bash）を生成する。

    責務: コマンド実行のみで配布物を配置できるスクリプトを作成する。
    入力: target, out_dir
    出力: (ps1パス, shパス)
    副作用: ファイルへの書き込み
    """
    ps1_content = f"""# deploy.ps1 — {target.name} 配布パッケージのデプロイスクリプト
#
# Usage: .\\deploy.ps1 -TargetRepo <対象リポジトリのパス>
#        .\\deploy.ps1 -TargetRepo C:\\Projects\\MyRepo
#
# このスクリプトは配布パッケージのファイルを対象リポジトリに配置します。
# 既存ファイルは上書きされます。

param(
    [Parameter(Mandatory=$true)]
    [string]$TargetRepo
)

$ErrorActionPreference = "Stop"
$SourceDir = $PSScriptRoot
$TargetRoot = $TargetRepo

Write-Host "配置先リポジトリ: $TargetRoot"
Write-Host "配布ソース: $SourceDir"

# .github フォルダ以下のファイルをコピーする
$GithubSource = Join-Path $SourceDir ".github"
$GithubTarget = Join-Path $TargetRoot ".github"

if (Test-Path $GithubSource) {{
    if (-not (Test-Path $GithubTarget)) {{
        New-Item -ItemType Directory -Path $GithubTarget -Force | Out-Null
    }}

    Get-ChildItem -Path $GithubSource -Recurse -File | ForEach-Object {{
        $RelPath = $_.FullName.Substring($GithubSource.Length).TrimStart("\\", "/")
        $Dest = Join-Path $GithubTarget $RelPath
        $DestDir = Split-Path $Dest -Parent

        if (-not (Test-Path $DestDir)) {{
            New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
        }}

        Copy-Item -Path $_.FullName -Destination $Dest -Force
        Write-Host "  コピー: $RelPath"
    }}
}}

Write-Host ""
Write-Host "✅ デプロイ完了。{target.name} フックが $TargetRoot に配置されました。"
Write-Host ""
Write-Host "次のステップ:"
Write-Host "  1. VS Code でリポジトリを開く"
Write-Host "  2. GitHub Copilot のフック設定を確認する"
Write-Host "  3. フックが正しく動作しているか Output チャンネルで確認する"
"""

    sh_content = f"""#!/usr/bin/env bash
# deploy.sh — {target.name} 配布パッケージのデプロイスクリプト
#
# Usage: bash deploy.sh <対象リポジトリのパス>
#        bash deploy.sh /path/to/MyRepo
#
# このスクリプトは配布パッケージのファイルを対象リポジトリに配置します。
# 既存ファイルは上書きされます。

set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Usage: bash deploy.sh <TargetRepo>" >&2
    exit 1
fi

SOURCE_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
TARGET_ROOT="$1"

echo "配置先リポジトリ: $TARGET_ROOT"
echo "配布ソース: $SOURCE_DIR"

GITHUB_SOURCE="$SOURCE_DIR/.github"
GITHUB_TARGET="$TARGET_ROOT/.github"

if [ -d "$GITHUB_SOURCE" ]; then
    mkdir -p "$GITHUB_TARGET"
    find "$GITHUB_SOURCE" -type f | while read -r src; do
        rel="${{src#$GITHUB_SOURCE/}}"
        dest="$GITHUB_TARGET/$rel"
        dest_dir="$(dirname "$dest")"
        mkdir -p "$dest_dir"
        cp -f "$src" "$dest"
        echo "  コピー: $rel"
    done
fi

echo ""
echo "✅ デプロイ完了。{target.name} フックが $TARGET_ROOT に配置されました。"
echo ""
echo "次のステップ:"
echo "  1. VS Code でリポジトリを開く"
echo "  2. GitHub Copilot のフック設定を確認する"
echo "  3. フックが正しく動作しているか Output チャンネルで確認する"
"""

    ps1_path = out_dir / "deploy.ps1"
    sh_path = out_dir / "deploy.sh"
    ps1_path.write_text(ps1_content, encoding="utf-8")
    sh_path.write_text(sh_content, encoding="utf-8")

    # シェルスクリプトに実行権限を付与
    sh_path.chmod(sh_path.stat().st_mode | 0o755)

    return ps1_path, sh_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    """コマンドライン引数を解析する。"""
    parser = argparse.ArgumentParser(
        description="フック・コンポーネントの配布用パッケージを生成する"
    )
    parser.add_argument(
        "target",
        help="配布対象のフック名（例: access-control）またはスクリプト名（例: access_control）",
    )
    parser.add_argument(
        "--out-dir",
        default="dist",
        help="配布物の出力先ディレクトリ（デフォルト: dist）",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="リポジトリルートのパス（デフォルト: カレントディレクトリ）",
    )
    return parser.parse_args()


def main() -> None:
    """エントリーポイント: 依存解析 → コピー → README生成 → デプロイスクリプト生成。"""
    args = _parse_args()
    repo_root = Path(args.repo_root).resolve()
    out_dir = Path(args.out_dir).resolve() / args.target

    print(f"対象: {args.target}")
    print(f"配布先: {out_dir}")
    print(f"リポジトリルート: {repo_root}")
    print()

    # 依存解析
    print("依存ファイルを解析中...")
    dist_target = find_hook_target(args.target, repo_root)
    print(f"  エントリーポイント: {len(dist_target.entrypoint_paths)} 件")
    print(f"  依存ファイル: {len(dist_target.dependency_paths)} 件")
    print(f"  設定ファイル: {len(dist_target.config_paths)} 件")
    print()

    # ファイルコピー（テスト除外）
    print("ファイルをコピー中...")
    copied, skipped = copy_files_to_dist(dist_target, out_dir, repo_root)
    print(f"  コピー: {len(copied)} 件")
    print(f"  テストファイル除外: {len(skipped)} 件")
    print()

    # README 生成
    print("README を生成中...")
    readme_path = generate_readme(dist_target, out_dir, copied, repo_root)
    print(f"  生成: {readme_path}")
    print()

    # デプロイスクリプト生成
    print("デプロイスクリプトを生成中...")
    ps1_path, sh_path = generate_deploy_scripts(dist_target, out_dir)
    print(f"  生成: {ps1_path}")
    print(f"  生成: {sh_path}")
    print()

    result = DistResult(
        out_dir=out_dir,
        copied_files=copied,
        readme_paths=[readme_path],
        deploy_script_ps1=ps1_path,
        deploy_script_sh=sh_path,
        skipped_test_files=skipped,
    )
    print("===== 完了 =====")
    print(result.summary())


if __name__ == "__main__":
    main()
