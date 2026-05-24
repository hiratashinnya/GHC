#!/usr/bin/env python3
"""distribute.py — 配布パッケージ生成のエントリーポイント。

責務: コマンドライン引数を解析し、各モジュールをオーケストレーションする。
     テスト関連ファイルの判定・除去はエージェント（distribute.agent.md）の責務。

Usage:
  python .github/scripts/distribute.py <target> [--out-dir dist] [--repo-root .]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# サブモジュールを sys.path に追加（同一ディレクトリ内のモジュールを参照するため）
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from dist_deps import find_hook_target
from dist_copy import copy_files_to_dist
from dist_readme import generate_readme
from dist_deploy import generate_deploy_scripts
from dist_models import DistResult


def _parse_args() -> argparse.Namespace:
    """コマンドライン引数を解析する。"""
    parser = argparse.ArgumentParser(description="フック・コンポーネントの配布用パッケージを生成する")
    parser.add_argument("target", help="配布対象のフック名（例: access-control）")
    parser.add_argument("--out-dir", default="dist", help="出力先ディレクトリ（デフォルト: dist）")
    parser.add_argument("--repo-root", default=".", help="リポジトリルート（デフォルト: .）")
    return parser.parse_args()


def main() -> None:
    """依存解析 → コピー → README生成 → デプロイスクリプト生成をオーケストレーションする。"""
    args = _parse_args()
    repo_root = Path(args.repo_root).resolve()
    out_dir = Path(args.out_dir).resolve() / args.target

    print(f"対象: {args.target}  配布先: {out_dir}")

    print("依存ファイルを解析中...")
    target = find_hook_target(args.target, repo_root)
    print(f"  エントリーポイント: {len(target.entrypoint_paths)} 件  "
          f"依存: {len(target.dependency_paths)} 件  "
          f"設定: {len(target.config_paths)} 件")

    print("ファイルをコピー中...")
    copied = copy_files_to_dist(target, out_dir, repo_root)
    print(f"  コピー: {len(copied)} 件")

    print("README を生成中...")
    readme_path = generate_readme(target, out_dir, copied, repo_root)

    print("デプロイスクリプトを生成中...")
    ps1_path, sh_path = generate_deploy_scripts(target, out_dir)

    result = DistResult(
        out_dir=out_dir,
        copied_files=copied,
        readme_paths=[readme_path],
        deploy_script_ps1=ps1_path,
        deploy_script_sh=sh_path,
    )
    print("\n===== 完了 =====")
    print(result.summary())


if __name__ == "__main__":
    main()
