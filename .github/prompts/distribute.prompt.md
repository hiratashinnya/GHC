---
description: "Use when you want to distribute (package) hooks, agents, skills, or other Copilot customizations for deployment to another repository. Runs the distribute workflow that resolves target type, analyzes dependencies, copies files, generates Japanese README, and creates deploy scripts. Trigger phrases: /distribute, distribute hook, distribute agent, distribute skill, create distribution package, export hook, package for distribution"
name: distribute
argument-hint: "<target-name> [--out-dir dist] [--repo-root .]"
---

# /distribute — 配布パッケージ作成スラッシュコマンド

GitHub Copilot カスタマイズファイル（フック・エージェント・スキル等）の配布パッケージを生成します。

## 使用方法

```
/distribute <target> [オプション]
```

### 引数

| 引数 | 説明 | 例 |
|------|------|----|
| `<target>` | 配布対象の名前（必須） | `access-control`, `reviewer`, `hooks-dev` |
| `--out-dir` | 出力先ディレクトリ（省略時: `dist`） | `--out-dir exports` |
| `--repo-root` | リポジトリルート（省略時: `.`） | `--repo-root /path/to/repo` |

### 使用例

```
# フックを配布する
/distribute access-control

# カスタム出力先
/distribute access-control --out-dir my-exports

```

---

## 実行手順

このコマンドを受け取ったら、以下の手順で配布パッケージを生成してください：

### Step 1: 対象の確認

ユーザーが指定した `<target>` を確認する：

- フック名の場合: `.github/hooks/<target>.json` が存在するか確認
- エージェント名の場合: `.github/agents/<target>.agent.md` が存在するか確認
- スキル名の場合: `.github/skills/<target>/SKILL.md` が存在するか確認

対象が見つからない場合は、利用可能な対象の一覧を表示してユーザーに選択を求める。

### Step 2: 方策比較と採用方針の確認

対応範囲をフック以外へ拡張する際は、以下を比較して **A 案（単一スクリプト拡張）** を採用する：

| 案 | 内容 | 利点 | 欠点 |
|----|------|------|------|
| A | `distribute.py` を hook/agent/skill 判定対応に拡張 | `/distribute` の UX と実装を一本化できる | スクリプトの責務が増える |
| B | 対象種別ごとに別スクリプト化 | 個別ロジックを分離しやすい | コマンド分岐と保守コストが増える |
| C | スクリプトは hook のみ、agent が手動補完 | 実装変更が最小 | 自動化一貫性が崩れ、再現性が下がる |

本ワークフローでは A 案を採用し、`distribute.py` で対象種別を自動解決する。

### Step 3: 依存関係の解析

`distribute.py` を実行して依存ファイルを自動解析する：

```bash
python .github/scripts/distribute.py <target> --out-dir <out-dir> --repo-root <repo-root>
```

解析結果を確認して、重要な依存ファイルが漏れていないかチェックする。

### Step 4: 配布パッケージの検証

生成されたパッケージを確認する：

1. `dist/<target>/README.md` を開き、以下が含まれているか検証する：
   - 配布物のフォルダ構成（ツリー表示）
   - 配置先のフォルダ構成
   - 各ファイルの配置先パス
   - 依存関係の一覧
   - セットアップ手順（deploy スクリプトの使い方）

2. `dist/<target>/deploy.ps1` と `dist/<target>/deploy.sh` が生成されているか確認する

3. テスト関連ファイルの取り扱いが配布ポリシーと一致しているか確認する（必要ならエージェントが手動除去）

### Step 5: 元ファイルの README 更新

対象に関連する元 README ファイルがある場合：

- フック: `.github/agents/README-<target>.md`（存在すれば）
- エージェント: `.github/agents/README-<target>.md`
- スキル: `.github/skills/<target>/README.md`

配布物の情報（フォルダ構成・デプロイ方法・依存関係）を元 README にも反映する。
**ただし、テスト関連情報は元 README に残す**。

### Step 6: 完了報告

以下の形式で結果を報告する：

```
✅ 配布パッケージを生成しました

📦 パッケージ: dist/<target>/
📄 README: dist/<target>/README.md
🚀 デプロイスクリプト:
   - Windows: dist/<target>/deploy.ps1
   - Linux/macOS: dist/<target>/deploy.sh

📋 含まれるファイル:
  - <ファイル一覧>

🚫 テスト関連ファイルの扱い:
  - <除外したファイル一覧>（または「除外なし」）

📘 使用方法:
  Windows: cd dist/<target> && .\deploy.ps1 -TargetRepo <配置先パス>
  Linux:   cd dist/<target> && bash deploy.sh <配置先パス>
```

---

## 提案機能

以下の追加機能が必要な場合は、ユーザーに提案してください：

| 機能 | 説明 |
|------|------|
| バージョニング | `dist/<target>-v1.0.0/` 形式での出力 |
| ZIP 圧縮 | 配布パッケージを `.zip` ファイルに圧縮する |
| チェックサム | SHA-256 チェックサムファイルの生成 |
| 複数対象の一括配布 | 複数のフック・エージェントをまとめてパッケージ化 |
| CHANGELOG 生成 | git log から変更履歴を自動生成 |
