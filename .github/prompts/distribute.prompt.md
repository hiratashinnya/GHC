---
description: "Use when you want to distribute (package) hooks, agents, skills, or other Copilot customizations for deployment to another repository. Analyzes dependencies, copies files, generates Japanese README and deploy scripts. Trigger phrases: /distribute, distribute hook, create distribution package, export hook, package for distribution"
name: distribute
argument-hint: "<target-name> [--out-dir dist] [--repo-root .] [--include-tests]"
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
| `--include-tests` | テスト関連ファイルも含める（省略時は除外） | `--include-tests` |

### 使用例

```
# フックを配布する
/distribute access-control

# カスタム出力先
/distribute access-control --out-dir my-exports

# テストファイルも含める（テスト機能を配布したい場合）
/distribute access-control --include-tests
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

### Step 2: 依存関係の解析

`distribute.py` を実行して依存ファイルを自動解析する：

```bash
python .github/scripts/distribute.py <target> --out-dir <out-dir> --repo-root <repo-root>
```

解析結果を確認して、重要な依存ファイルが漏れていないかチェックする。

### Step 3: 配布パッケージの検証

生成されたパッケージを確認する：

1. `dist/<target>/README.md` を開き、以下が含まれているか検証する：
   - 配布物のフォルダ構成（ツリー表示）
   - 配置先のフォルダ構成
   - 各ファイルの配置先パス
   - 依存関係の一覧
   - セットアップ手順（deploy スクリプトの使い方）

2. `dist/<target>/deploy.ps1` と `dist/<target>/deploy.sh` が生成されているか確認する

3. テストファイルが含まれていないか確認する（`--include-tests` が指定されていない場合）

### Step 4: 元ファイルの README 更新

対象に関連する元 README ファイルがある場合：

- フック: `.github/agents/README-<target>.md`（存在すれば）
- エージェント: `.github/agents/README-<target>.md`
- スキル: `.github/skills/<target>/README.md`

配布物の情報（フォルダ構成・デプロイ方法・依存関係）を元 README にも反映する。
**ただし、テスト関連情報は元 README に残す**。

### Step 5: 完了報告

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

🚫 除外されたテストファイル:
  - <ファイル一覧>（または「なし」）

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
