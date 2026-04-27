# 残件リスト

最終更新: 2026-04-26

---

## 1. Dashboard-Pipeline SCAN スクリプト化

**出典**: memo.md  
**優先度**: 高

`dashboard-pipeline/SKILL.md` の Step 3（`iter/` 配下の未マージ承認済みdiff検出）を AI 判断から Python スクリプトに切り出す。

### 仕様

| 項目 | 内容 |
| ---- | ---- |
| スクリプトパス | `.github/scripts/scan_unmerged_diffs.py` |
| 入力 | `--iter-dir`（デフォルト: `iter`）、`--docs-dir`（デフォルト: `docs`） |
| 出力（stdout） | JSON: `{ "unmerged": [ { "path": "...", "iteration": N, "phase": "...", "base-version": "..." } ] }` |
| デバッグ | `scan_unmerged_diffs.debug` ファイルの有無で切替、ログは `scan_unmerged_diffs.debug.log` に出力 |
| 対象ファイル | `iter/iter*/phase*/*.md` で `status: approved` かつ `doc-kind: diff` のもの |

### 関連変更

- `dashboard-pipeline/SKILL.md` Step 3 を AI スキャンからスクリプト呼び出しに置き換える
- スクリプトに対応する README または docstring を記載する

---

## 2. `dashboard-pipeline/SKILL.md` Prerequisites 修正 ⇒修正済み

**出典**: memo.md  
**優先度**: 中

Step 1 はすでに `patch_dashboard.py` を直接呼び出す形になっているが、Prerequisites セクションに `build_status_matrix.py` と `extract_bottlenecks.py` の記載が残っている。実態と齟齬があるため削除する。

### 修正箇所

```
.github/skills/dashboard-pipeline/SKILL.md
```

**変更前（Prerequisites）:**
```
- Scripts `build_status_matrix.py`, `extract_bottlenecks.py`, and `patch_dashboard.py` exist under `.github/scripts/`
```

**変更後（Prerequisites）:**
```
- Script `patch_dashboard.py` exists under `.github/scripts/`
```

---

## 3. フェーズ別サブエージェント作成（6本）

**出典**: plan-systemDevWorkflow.prompt.md（🚧 一部実装 セクション）  
**優先度**: 中〜低

オーケストレータが各フェーズの実作業を委譲するサブエージェントが未作成。

| エージェント名 | ファイルパス | 対象フェーズ |
| -------------- | ------------ | ------------ |
| requirements-agent | `.github/agents/requirements-agent.agent.md` | フェーズ1: 要件定義 |
| basic-design-agent | `.github/agents/basic-design-agent.agent.md` | フェーズ2: 基本設計 |
| detailed-design-agent | `.github/agents/detailed-design-agent.agent.md` | フェーズ3: 詳細設計 |
| implementation-agent | `.github/agents/implementation-agent.agent.md` | フェーズ4: 実装（TDD対応） |
| testing-agent | `.github/agents/testing-agent.agent.md` | フェーズ5: テスト |
| release-agent | `.github/agents/release-agent.agent.md` | フェーズ6: リリース |

### 各エージェントの共通要件

- オーケストレータからの委譲を受けて当該フェーズ内の①〜⑤プロセスを実行する
- 差分ドキュメントを `iter/iterN/phaseX/` に作成し、承認後に正本へマージする
- `dashboard-sync` スキルでダッシュボードを更新する
- フェーズゲートチェック（`approval-required: true` 文書の承認状態確認）を行う
- `routing-on-failure` スキルで①⑤NG時の差し戻し先を判定する
- 各エージェントに対応する日本語 README（`README-{agent-name}.md`）を添える

### `implementation-agent` 固有要件

- TDD フロー（Red→Green→Refactor サイクル）に対応する
- 詳細設計の承認済みテストケース設計書を入力として受け取る
- コード本体を `src/` 配下に配置し、`docs/implementation/04-artifact.md` にサマリ＋参照リストのみ記載する

## 4. iter/phaseNのフォルダ名をフェーズ名に変更したい

scan_unmerged_diffs.py 内の PHASE_MAP を参照。
iter/phaseN → docs/<phase-dir> のマッピングを定義しているが、そもそもフォルダ名がフェーズ名になっていたら不要。正本との整合性を取るためにも修正したい。
スクリプト、エージェント、Skill、ドキュメントテンプレートなど、関連箇所が多岐にわたるため、影響範囲を十分に確認してから実施すること。