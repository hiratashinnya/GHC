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

import _lib
from dist_deps import find_distribution_target
from dist_copy import copy_files_to_dist
from dist_readme import generate_readme
from dist_deploy import generate_deploy_scripts
from dist_models import DistResult

_SCRIPT_ID = "distribute"


def _parse_args() -> argparse.Namespace:
    """コマンドライン引数を解析する。"""
    parser = argparse.ArgumentParser(description="フック・エージェント・スキルの配布用パッケージを生成する")
    parser.add_argument("target", help="配布対象名（例: access-control / reviewer / hooks-dev）")
    parser.add_argument("--out-dir", default="dist", help="出力先ディレクトリ（デフォルト: dist）")
    parser.add_argument("--repo-root", default=".", help="リポジトリルート（デフォルト: .）")
    return parser.parse_args()


def _run_distribution(args: argparse.Namespace) -> DistResult:
    """配布処理本体を実行し DistResult を返す。"""
    repo_root = Path(args.repo_root).resolve()
    out_dir = Path(args.out_dir).resolve() / args.target

    _lib.debug_log(_SCRIPT_ID, "start", target=args.target, out_dir=str(out_dir), repo_root=str(repo_root))
    target = find_distribution_target(args.target, repo_root)
    _lib.debug_log(
        _SCRIPT_ID,
        "resolved-target",
        target_type=target.target_type,
        entrypoints=len(target.entrypoint_paths),
        dependencies=len(target.dependency_paths),
        configs=len(target.config_paths),
    )

    copied = copy_files_to_dist(target, out_dir, repo_root)
    readme_path = generate_readme(target, out_dir, copied, repo_root)
    ps1_path, sh_path = generate_deploy_scripts(target, out_dir)

    return DistResult(
        out_dir=out_dir,
        copied_files=copied,
        readme_paths=[readme_path],
        deploy_script_ps1=ps1_path,
        deploy_script_sh=sh_path,
    )


def _result_json(result: DistResult, target_name: str) -> dict:
    """DistResult を機械可読 JSON に変換する。"""
    return {
        "success": True,
        "target": target_name,
        "outDir": _lib.norm(result.out_dir),
        "copiedCount": len(result.copied_files),
        "copiedFiles": [_lib.norm(path) for path in result.copied_files],
        "readmePaths": [_lib.norm(path) for path in result.readme_paths],
        "deployScripts": {
            "ps1": _lib.norm(result.deploy_script_ps1) if result.deploy_script_ps1 else None,
            "sh": _lib.norm(result.deploy_script_sh) if result.deploy_script_sh else None,
        },
        "summary": result.summary(),
    }


def main() -> None:
    """依存解析 → コピー → README生成 → デプロイスクリプト生成を実行し JSON 出力する。"""
    try:
        args = _parse_args()
        result = _run_distribution(args)
        _lib.debug_log(_SCRIPT_ID, "done", copied=len(result.copied_files), out_dir=str(result.out_dir))
        _lib.out_json(_result_json(result, args.target))
    except Exception as exc:
        _lib.debug_log(_SCRIPT_ID, "error", error=str(exc))
        _lib.out_err(str(exc))


if __name__ == "__main__":
    main()
