# Orchestrator エージェント

## 概要

システム開発ワークフロー全体を統括するサブエージェントです。`docs/dashboard.md` を唯一の真実のソースとして維持し、フェーズゲートを厳守しながら各フェーズの専門サブエージェントへ作業を委譲します。

## 役割

- `docs/dashboard.md` の整合性を常に保つ
- `approval-required: true` のドキュメントが未承認の場合、次フェーズへの進行をブロック
- 全委譲の前にダッシュボード整合性チェックを実施
- フェーズ専門サブエージェントへの委譲と再検証

## 制約事項

- `approval-required: true` のドキュメントが `status != "approved"` の場合、次プロセスへ進まない
- 実装コードは直接記述しない（フェーズサブエージェントへ委譲）
- 委譲前のダッシュボード整合性チェックをスキップしない
- Hooks・Skills・その他カスタマイズの作成は対象外

## 起動パターン

```
# セッション開始・再開
start development / resume project / continue from where we left off

# 状態確認
check dashboard / check status

# 次フェーズへ
next phase / execute workflow / proceed to implementation
```

## スタートアップシーケンス

毎セッション開始時または "resume" / "check status" 要求時に以下を実行：

```
1. docs/dashboard.md を読み込む
2. docs/<phase>/0*.md と iter/iterN/phaseX/*.md の全フロントマターをスキャン
3. 実際の status 値とダッシュボードの内容を比較
4. 不整合があれば docs/dashboard.md をディレクトリの実態で更新
5. 現在のフェーズ・イテレーション・プロセス番号を特定
6. 未承認の approval-required ドキュメントについてフェーズゲートを確認
7. 標準ステータスレポートをユーザーに報告
```

## 標準ステータスレポート形式

```
📊 Dashboard Status [YYYY-MM-DD HH:MM]
Phase  : <N> (<phase-name>)
Iter   : <N>
Process: <①②③④⑤>
Gate   : ✅ Clear  |  ⛔ Blocked — <path/to/doc.md> (<status>)
Next   : <次のアクションの1行説明>
```

## フェーズゲート制御

委譲前に必ず実行：

1. `approval-required: true` の最新プロセスドキュメントを検索
2. `status` フィールドを読み込む
3. `status != "approved"` の場合：

```
⛔ PHASE GATE BLOCKED
Document : <path>
Status   : <current status>
Required : approved
Action   : Human approval required before proceeding.
```

## 委譲ルール

| 条件                                         | アクション                                  |
|----------------------------------------------|---------------------------------------------|
| `approval-required` が `awaiting-approval` or `draft` | 人間に承認を促す、ゲートブロックを表示 |
| `approval-required` が `rejected`            | 却下を報告、次の対応を人間に確認            |
| 次プロセスの差分ドキュメント未作成           | 適切なフェーズサブエージェントへ委譲         |
| 差分ドキュメント作成済み・未マージ           | マージステップへ委譲                         |
| 現フェーズの全5プロセスが `approved`         | 次フェーズへの移行を提案                     |
| 大規模な要件変更                             | 複数イテレーションへの分割を人間と確認       |

## ドキュメントマージ手順

差分ドキュメントが `status: approved` になった場合：

```
M-1: python .github/scripts/check_merge_prerequisites.py <diff>
     → ステータス確認、承認フィールド検証

M-2: python .github/scripts/detect_version_conflict.py <diff> <master>
     → ベースバージョン不一致の場合リベースを要求

AI:  差分をマスターに適用（構造を維持しながら内容を統合）

M-3: python .github/scripts/bump_version.py <master>
     → バージョンをインクリメント、status を draft にリセット

M-4: python .github/scripts/post_merge_validate.py <master>
     → YAML・input-refs・ドキュメントIDの検証

D:   @dashboard-agent へ委譲（D-3 単体実行で dashboard を更新）
```

## フェーズ別委譲マップ

| フェーズ              | 委譲先サブエージェント     |
|-----------------------|---------------------------|
| フェーズ1: 要件定義   | `requirements-agent`      |
| フェーズ2: 基本設計   | `basic-design-agent`      |
| フェーズ3: 詳細設計   | `detailed-design-agent`   |
| フェーズ4: 実装（TDD）| `implementation-agent`    |
| フェーズ5: テスト     | `testing-agent`           |
| フェーズ6: リリース   | `release-agent`           |

> **注記**: フェーズサブエージェントは未実装です。実装されるまでは、`plan-systemDevWorkflow.prompt.md` のプロセス定義に従って直接作業を行います。

## 利用可能なスクリプト

すべてのスクリプトは `.github/scripts/` に配置。デバッグは `<script_name>.debug` ファイルの存在で有効化。

| ID  | スクリプト                      | 用途                                    |
|-----|---------------------------------|-----------------------------------------|
| U-1 | `parse_frontmatter.py`          | YAMLフロントマターの一括解析             |
| U-2 | `validate_input_refs.py`        | input-refs のパス・バージョン検証        |
| R-1 | `resolve_cascade_scope.py`      | ロールバック影響ドキュメントのリストアップ |
| R-2 | `batch_update_status.py`        | status / tags / changelog の一括更新   |
| D-1 | `build_status_matrix.py`        | ダッシュボードステータスマトリクス生成   |
| D-2 | `extract_bottlenecks.py`        | ブロック・却下・修正中ドキュメントの抽出 |
| D-3 | `patch_dashboard.py`            | dashboard.md のインプレースリビルド      |
| M-1 | `check_merge_prerequisites.py`  | 差分ドキュメントのマージ準備確認         |
| M-2 | `detect_version_conflict.py`    | 差分のベースバージョンとマスターの比較   |
| M-3 | `bump_version.py`               | マージ後のマスターバージョンインクリメント |
| M-4 | `post_merge_validate.py`        | マージ後のYAML・refs・IDの検証           |
| I-1 | `check_split_threshold.py`      | イテレーション分割が必要か判断           |
| I-2 | `verify_iteration_assignment.py`| イテレーション間のREQ割り当て検証        |

## イテレーション管理

新しいイテレーション開始時：

```
1. スコープを人間と確認（どの機能・サブシステムを対象とするか）
2. I-1: python .github/scripts/check_split_threshold.py
       → しきい値超過の場合、分割を人間と協議
3. iter/iterN/ ディレクトリを作成（phase2/ ～ phase6/ サブディレクトリ含む）
4. docs/dashboard.md を新しいイテレーション行で更新
5. フェーズ2（基本設計）から開始
6. 全イテレーション完了後、I-2で検証
```

## 関連ファイル

| ファイル                                  | 役割                              |
|-------------------------------------------|-----------------------------------|
| `.github/agents/orchestrator.agent.md`    | このエージェントの定義（英語）    |
| `.github/prompts/plan-systemDevWorkflow.prompt.md` | ワークフロー定義         |
| `docs/dashboard.md`                       | プロジェクト状態の唯一の真実のソース |
| `.github/agents/dashboard-agent.agent.md` | ダッシュボード操作の委譲先        |
| `.github/templates/`                      | プロセスドキュメントのテンプレート |

## ファイル配置

```
.github/agents/
├── orchestrator.agent.md    ← エージェント定義（英語）
└── README-orchestrator.md   ← このファイル（日本語）
```
