#!/usr/bin/env python3
"""dist_deploy.py — 再配置用デプロイスクリプト（PS1 / Bash）を生成するモジュール。

責務: コマンド実行のみで配布物を配置先リポジトリに展開できるスクリプトを作成する。
入力: DistTarget, out_dir
出力: (ps1パス, shパス)
副作用: ファイルへの書き込み・権限変更
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

from dist_models import DistTarget


def _ps1_content(target_name: str) -> str:
    """PowerShell デプロイスクリプトの本文を返す。

    責務: Windows 環境向けのファイル配置スクリプトを生成する。
    入力: target_name — フック名
    出力: PS1 スクリプト文字列
    副作用: なし
    """
    return f"""# deploy.ps1 — {target_name} 配布パッケージのデプロイスクリプト
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
Write-Host "✅ デプロイ完了。{target_name} の配布ファイルが $TargetRoot に配置されました。"
Write-Host ""
Write-Host "次のステップ:"
Write-Host "  1. VS Code でリポジトリを開く"
Write-Host "  2. GitHub Copilot のフック設定を確認する"
Write-Host "  3. フックが正しく動作しているか Output チャンネルで確認する"
"""


def _sh_content(target_name: str) -> str:
    """Bash デプロイスクリプトの本文を返す。

    責務: Linux / macOS 環境向けのファイル配置スクリプトを生成する。
    入力: target_name — フック名
    出力: Bash スクリプト文字列
    副作用: なし
    """
    return f"""#!/usr/bin/env bash
# deploy.sh — {target_name} 配布パッケージのデプロイスクリプト
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
echo "✅ デプロイ完了。{target_name} の配布ファイルが $TARGET_ROOT に配置されました。"
echo ""
echo "次のステップ:"
echo "  1. VS Code でリポジトリを開く"
echo "  2. GitHub Copilot のフック設定を確認する"
echo "  3. フックが正しく動作しているか Output チャンネルで確認する"
"""


def generate_deploy_scripts(target: DistTarget, out_dir: Path) -> Tuple[Path, Path]:
    """再配置用デプロイスクリプト（PS1 / Bash）を out_dir に生成する。

    責務: コマンド実行のみで配布物を配置できるスクリプトを作成する。
    入力: target, out_dir
    出力: (ps1パス, shパス)
    副作用: ファイルへの書き込み・実行権限付与
    """
    ps1_path = out_dir / "deploy.ps1"
    sh_path = out_dir / "deploy.sh"

    ps1_path.write_text(_ps1_content(target.name), encoding="utf-8")
    sh_path.write_text(_sh_content(target.name), encoding="utf-8")
    sh_path.chmod(sh_path.stat().st_mode | 0o755)

    return ps1_path, sh_path
