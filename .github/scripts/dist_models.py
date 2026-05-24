#!/usr/bin/env python3
"""dist_models.py — 配布処理で使うデータクラスとパス定数。

責務: DistTarget / DistResult の定義とリポジトリ内の固定パス定数を提供する。
入力: なし（モジュールインポート用）
出力: なし（モジュールインポート用）
副作用: なし
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set

# ---------------------------------------------------------------------------
# Repository-relative path constants
# ---------------------------------------------------------------------------

HOOKS_ROOT = Path(".github/hooks")
SCRIPTS_ROOT = HOOKS_ROOT / "scripts"
ENTRYPOINTS_DIR = SCRIPTS_ROOT / "entrypoints"
CONFIG_DIR = HOOKS_ROOT / "config"


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
        """全ファイル/ディレクトリパスのリストを返す（重複除去済み）。

        責務: hook_json・entrypoints・deps・config を一本のリストに統合する。
        入力: なし
        出力: 重複のないパスリスト
        副作用: なし
        """
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

    def summary(self) -> str:
        """処理結果のサマリー文字列を返す。

        責務: コンソール出力用のサマリーテキストを組み立てる。
        入力: なし
        出力: 複数行のサマリー文字列
        副作用: なし
        """
        lines = [
            f"配布先: {self.out_dir}",
            f"コピーされたファイル数: {len(self.copied_files)}",
            f"生成されたREADME: {', '.join(str(p) for p in self.readme_paths)}",
        ]
        if self.deploy_script_ps1:
            lines.append(f"デプロイスクリプト(PS1): {self.deploy_script_ps1}")
        if self.deploy_script_sh:
            lines.append(f"デプロイスクリプト(SH): {self.deploy_script_sh}")
        return "\n".join(lines)
