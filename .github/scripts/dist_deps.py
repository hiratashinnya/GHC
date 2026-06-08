#!/usr/bin/env python3
"""dist_deps.py — 配布対象の依存ファイルを解析するモジュール。

責務: Python import グラフを再帰的に追跡し、配布に必要な全ファイルを収集する。
入力: エントリーポイントパス・探索ディレクトリ一覧
出力: 依存ファイル/ディレクトリパスのリスト
副作用: なし（ファイル読み取りのみ）
"""

from __future__ import annotations

import ast
import json
import re
import shlex
from pathlib import Path
from typing import List, Optional, Set

from dist_models import (
    CONFIG_DIR,
    ENTRYPOINTS_DIR,
    HOOKS_ROOT,
    SCRIPTS_ROOT,
    DistTarget,
)


def _extract_python_imports(py_path: Path) -> Set[str]:
    """Python ファイルから import されているモジュール名のセットを返す。

    責務: AST パース + フォールバック正規表現で import 文を抽出する。
    入力: py_path — 解析対象の Python ファイルパス
    出力: トップレベルモジュール名のセット
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
        source = py_path.read_text(encoding="utf-8")
        for match in re.finditer(r"^(?:from|import)\s+([\w.]+)", source, re.MULTILINE):
            imports.add(match.group(1).split(".")[0])
    return imports


def _find_module_path(module_name: str, search_dirs: List[Path]) -> Optional[Path]:
    """モジュール名からファイルパスまたはパッケージディレクトリを解決する。

    責務: search_dirs を順に探索し、最初に見つかったモジュールパスを返す。
    入力: module_name — モジュール名, search_dirs — 探索対象ディレクトリ
    出力: ファイルパスまたはパッケージディレクトリ、見つからなければ None
    副作用: なし
    """
    for search_dir in search_dirs:
        candidate = search_dir / f"{module_name}.py"
        if candidate.exists():
            return candidate
        pkg_dir = search_dir / module_name
        if pkg_dir.is_dir():
            return pkg_dir
    return None


def resolve_dependencies(
    entry: Path,
    search_dirs: List[Path],
    visited: Optional[Set[Path]] = None,
) -> List[Path]:
    """エントリーポイントの依存ファイルを再帰的に解決する。

    責務: import グラフを深さ優先探索し、全依存ファイルを収集する。
          パッケージディレクトリはそのままリストに追加し、中は再帰しない。
    入力: entry — 起点, search_dirs — モジュール探索ディレクトリ
    出力: 依存パスリスト（重複なし、topological 順）
    副作用: なし
    """
    if visited is None:
        visited = set()
    if entry in visited:
        return []
    visited.add(entry)

    # パッケージディレクトリは再帰しない
    if entry.is_dir():
        return []

    deps: List[Path] = []
    for module_name in sorted(_extract_python_imports(entry)):
        module_path = _find_module_path(module_name, search_dirs)
        if module_path is None or module_path in visited:
            continue
        deps.extend(resolve_dependencies(module_path, search_dirs, visited))
        deps.append(module_path)

    return deps


def _build_search_dirs(scripts_root: Path, repo_root: Path) -> List[Path]:
    """モジュール探索ディレクトリのリストを返す。

    責務: フック・スクリプトの標準モジュールパスを一括で定義する。
    入力: scripts_root, repo_root
    出力: 探索ディレクトリのリスト
    副作用: なし
    """
    return [
        scripts_root / "core",
        scripts_root / "access_control",
        scripts_root / "tooling",
        scripts_root / "shared",
        scripts_root,
        repo_root / ".github" / "scripts",
    ]


def _resolve_relative_token(token: str, repo_root: Path) -> Path:
    """トークンの先頭にある相対パス指定 './' を安全に除去して絶対パスを解決する。"""
    clean_token = token[2:] if token.startswith("./") else token
    clean_path = Path(clean_token)
    return clean_path if clean_path.is_absolute() else (repo_root / clean_token)


def _find_config_paths_from_json(hook_json_path: Path, repo_root: Path) -> List[Path]:
    """フック JSON 内のコマンド文字列から設定ファイルパスを抽出する。

    責務: JSON の command フィールドを解析し、config パスを収集する。
    入力: hook_json_path, repo_root
    出力: 存在する設定ファイルパスのリスト
    副作用: なし
    """
    config_paths: List[Path] = []
    try:
        hook_data = json.loads(hook_json_path.read_text(encoding="utf-8"))
        for _event, commands in hook_data.get("hooks", {}).items():
            for cmd in commands:
                for token in shlex.split(cmd.get("command", "")):
                    if token.endswith(".json") and "config" in token:
                        cfg = _resolve_relative_token(token, repo_root)
                        if cfg.exists():
                            config_paths.append(cfg)
    except (ValueError, json.JSONDecodeError, KeyError):
        pass
    return config_paths


def _find_entrypoints_from_hook_json(hook_json_path: Path, repo_root: Path) -> List[Path]:
    """フック JSON の command から実際の Python エントリーポイントを抽出する。"""
    entrypoints: List[Path] = []
    try:
        hook_data = json.loads(hook_json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return entrypoints

    for commands in hook_data.get("hooks", {}).values():
        for cmd in commands:
            command_text = cmd.get("command", "")
            try:
                tokens = shlex.split(command_text)
            except ValueError:
                continue
            script_token = next((token for token in tokens if token.endswith(".py")), None)
            if script_token is None:
                continue
            candidate = _resolve_relative_token(script_token, repo_root)
            if candidate.exists() and candidate not in entrypoints:
                entrypoints.append(candidate)

    return entrypoints


def find_hook_target(target_name: str, repo_root: Path) -> DistTarget:
    """対象名からフックの DistTarget を構築する。

    責務: フック JSON・エントリーポイント・依存ファイル・設定ファイルを発見する。
    入力: target_name — フック名（例: access-control）, repo_root
    出力: DistTarget
    副作用: なし
    """
    hooks_root = repo_root / HOOKS_ROOT
    scripts_root = repo_root / SCRIPTS_ROOT
    entrypoints_dir = repo_root / ENTRYPOINTS_DIR
    config_dir = repo_root / CONFIG_DIR
    script_name = target_name.replace("-", "_")

    # フック JSON
    hook_json_path: Optional[Path] = None
    for json_name in (target_name, target_name.replace("_", "-")):
        candidate = hooks_root / f"{json_name}.json"
        if candidate.exists():
            hook_json_path = candidate
            break

    # エントリーポイント（hook JSON の command から優先抽出）
    entrypoint_paths: List[Path] = []
    if hook_json_path:
        entrypoint_paths = _find_entrypoints_from_hook_json(hook_json_path, repo_root)
    if not entrypoint_paths:
        ep = entrypoints_dir / f"{script_name}.py"
        entrypoint_paths = [ep] if ep.exists() else list(entrypoints_dir.glob(f"*{script_name}*.py"))

    # 依存ファイル
    search_dirs = _build_search_dirs(scripts_root, repo_root)
    dependency_paths: List[Path] = []
    for ep_path in entrypoint_paths:
        for dep in resolve_dependencies(ep_path, search_dirs):
            if dep not in dependency_paths:
                dependency_paths.append(dep)

    # 設定ファイル
    config_paths: List[Path] = []
    if hook_json_path:
        config_paths = _find_config_paths_from_json(hook_json_path, repo_root)
    for cfg_name in (target_name, script_name):
        cfg = config_dir / f"{cfg_name}.json"
        if cfg.exists() and cfg not in config_paths:
            config_paths.append(cfg)

    return DistTarget(
        name=target_name,
        target_type="hook",
        hook_json_path=hook_json_path,
        entrypoint_paths=entrypoint_paths,
        dependency_paths=dependency_paths,
        config_paths=config_paths,
    )


def _find_markdown_local_paths(source_path: Path, repo_root: Path) -> List[Path]:
    """Markdown 内のローカルリンク先パスを収集する。"""
    result: List[Path] = []
    text = source_path.read_text(encoding="utf-8")
    for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
        path_text = link.strip()
        if (
            not path_text
            or path_text.startswith("#")
            or "://" in path_text
            or path_text.startswith("mailto:")
        ):
            continue
        candidate = (source_path.parent / path_text).resolve()
        try:
            candidate.relative_to(repo_root)
        except ValueError:
            continue
        if candidate.exists() and candidate not in result:
            result.append(candidate)
    return result


def find_agent_target(target_name: str, repo_root: Path) -> DistTarget:
    """対象名からエージェントの DistTarget を構築する。"""
    agent_path = repo_root / ".github" / "agents" / f"{target_name}.agent.md"
    if not agent_path.exists():
        return DistTarget(name=target_name, target_type="agent")

    dependency_paths = _find_markdown_local_paths(agent_path, repo_root)
    agent_readme = repo_root / ".github" / "agents" / f"README-{target_name}.md"
    if agent_readme.exists() and agent_readme not in dependency_paths:
        dependency_paths.append(agent_readme)

    return DistTarget(
        name=target_name,
        target_type="agent",
        entrypoint_paths=[agent_path],
        dependency_paths=dependency_paths,
    )


def find_skill_target(target_name: str, repo_root: Path) -> DistTarget:
    """対象名からスキルの DistTarget を構築する。"""
    skill_dir = repo_root / ".github" / "skills" / target_name
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return DistTarget(name=target_name, target_type="skill")

    dependency_paths = _find_markdown_local_paths(skill_md, repo_root)
    return DistTarget(
        name=target_name,
        target_type="skill",
        entrypoint_paths=[skill_dir],
        dependency_paths=dependency_paths,
    )


def find_distribution_target(target_name: str, repo_root: Path) -> DistTarget:
    """対象名から配布ターゲットを解決する（hook / agent / skill）。"""
    hook_target = find_hook_target(target_name, repo_root)
    if hook_target.hook_json_path is not None:
        return hook_target

    agent_target = find_agent_target(target_name, repo_root)
    if agent_target.entrypoint_paths:
        return agent_target

    skill_target = find_skill_target(target_name, repo_root)
    if skill_target.entrypoint_paths:
        return skill_target

    raise FileNotFoundError(
        f"Target '{target_name}' was not found as hook(.github/hooks/*.json), "
        "agent(.github/agents/*.agent.md), or skill(.github/skills/*/SKILL.md)."
    )
