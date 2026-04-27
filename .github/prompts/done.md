# 対応済みリスト

最終更新: 2026-04-26

---

## memo.md 由来

### `_dashboard.py` 関数リネーム

| 旧名 | 新名 | 状態 |
| ---- | ---- | ---- |
| `_emoji_for` | `_resolve_status_emoji` | ✅ 完了 |
| `build_matrix_md` | `build_status_matrix_md` | ✅ 完了 |

### `dashboard-pipeline/SKILL.md` Step 1 修正

`extract_bottlenecks.py` と `build_status_matrix.py` を個別に呼び出す形から、`patch_dashboard.py` を直接呼び出す自己完結型に変更済み。

---

## plan-systemDevWorkflow.prompt.md 由来

### 設計・仕様策定

| 項目 | 成果物 |
| ---- | ------ |
| フェーズ一覧と①〜⑤の適用方針設計 | テンプレート・ディレクトリ構成に反映済み |
| イテレーション方針設計 | オーケストレータの委譲ルール・`iter/` ディレクトリ構成に反映済み |
| 正本と差分ドキュメント設計 | `.github/templates/diff-document.md`、`docs/`・`iter/` ディレクトリ作成済み |
| I/O フォーマット規格（共通 YAML フロントマター） | `.github/templates/0N-*.md` 全テンプレートに反映済み |
| ドキュメントツリー実体化 | `docs/<phase>/`・`iter/`・`src/` を `.gitkeep` で作成済み |
| TDD フロー設計 | `04-artifact.md` テンプレートのテストケース設計セクション・オーケストレータのフロー説明に反映済み |
| 要件定義フェーズ成果物分割設計 | `04-artifact.md` を概要版に修正、`04-artifact-iterN.md` テンプレート作成済み |
| 詳細設計フェーズ 3 層分割構造設計 | テンプレート 13 ファイル作成済み（旧モノリシックテンプレート削除済み） |
| 各プロセス責務定義 | オーケストレータ・テンプレートに反映済み |

### フック実装

| フック | 実装ファイル |
| ------ | ------------ |
| PreToolUse フェーズゲート強制 | `.github/hooks/phase-gate.json` + `.github/hooks/scripts/check_phase_gate.py` |
| PostToolUse ダッシュボード自動更新 | `.github/hooks/dashboard-sync.json` + `.github/hooks/scripts/post_tool_dashboard_sync.py` |
| フック共通デバッグロギング | `.github/hooks/scripts/debug_logging.py` |

### スクリプト実装（`.github/scripts/`）

| # | スクリプト | 区分 |
| --- | ---------- | ---- |
| U-1 | `parse_frontmatter.py` | 共通ユーティリティ |
| U-2 | `validate_input_refs.py` | 共通ユーティリティ |
| H-1 | `check_phase_gate.py`（hooks/scripts/） | Hook 専用 |
| R-1 | `resolve_cascade_scope.py` | routing-on-failure 由来 |
| R-2 | `batch_update_status.py` | routing-on-failure 由来 |
| D-3 | `patch_dashboard.py` | dashboard-sync 由来（D-1・D-2 処理を内包） |
| D-1 | `build_status_matrix.py` | dashboard-sync 由来（単体補助用） |
| D-2 | `extract_bottlenecks.py` | dashboard-sync 由来（単体補助用） |
| M-1 | `check_merge_prerequisites.py` | doc-merge 由来 |
| M-2 | `detect_version_conflict.py` | doc-merge 由来 |
| M-3 | `bump_version.py` | doc-merge 由来 |
| M-4 | `post_merge_validate.py` | doc-merge 由来 |
| I-1 | `check_split_threshold.py` | iteration-splitting 由来 |
| I-2 | `verify_iteration_assignment.py` | iteration-splitting 由来 |

### 共通ライブラリ（`.github/scripts/_lib/`）

| モジュール | 責務 |
| ---------- | ---- |
| `_config.py` | 定数・設定値 |
| `_debug.py` | デバッグロギング |
| `_io.py` | ファイル入出力 |
| `_frontmatter.py` | YAML フロントマター解析 |
| `_paths.py` | パス解決ユーティリティ |
| `_dashboard.py` | ステータスマトリクス・ボトルネック生成 |

### スキル実装（`.github/skills/`）

| スキル名 | 用途 |
| -------- | ---- |
| `dashboard-sync` | フェーズ別ダッシュボード確認・更新手順（6 フェーズ統合） |
| `dashboard-pipeline` | D-3 呼び出し → 未マージ diff 検出 → 次アクション生成 |
| `routing-on-failure` | ①⑤NG 時の差し戻し先判定 |
| `doc-merge` | 差分→正本マージ手順 |
| `iteration-splitting` | 大規模要求のイテレーション分割基準・手順 |

### エージェント実装（`.github/agents/`）

| エージェント名 | 用途 |
| -------------- | ---- |
| `orchestrator` | SDLC 全フェーズのオーケストレーション・フェーズゲート管理 |
| `dashboard-agent` | D-pipeline 実行・未マージ diff 検出・ステータスレポート |
| `reviewer` | Copilot カスタマイズファイルのレビュー・検証 |
| `scaffold` | Copilot カスタマイズファイルの新規作成 |

### ダッシュボード

| 項目 | 状態 |
| ---- | ---- |
| テンプレート（`.github/templates/dashboard.md`） | ✅ 作成済み |
| 実体ファイル（`docs/dashboard.md`） | ✅ 作成済み |
| PostToolUse フックによる自動更新 | ✅ 実装済み |
