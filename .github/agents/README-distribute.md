# distribute エージェント

## 概要

フック・エージェント・スキル・プロンプトなど GitHub Copilot カスタマイズファイルを
他のリポジトリへ配布するための **配布パッケージ作成専門エージェント**です。

依存関係の自動解析からファイルコピー・README 生成・デプロイスクリプト生成まで、
配布に必要な一連の作業を自動化します。

---

## 主な機能

| 機能 | 説明 |
|------|------|
| 依存関係の解析 | Python の import 文を再帰的に追跡し、必要なモジュールをすべて収集する |
| ファイルコピー | `dist/<name>/` 以下に元のパス構成を維持してコピーする |
| テスト除去 | テスト関連ファイル（`test_*.py`, `testresult.md` 等）を配布物から自動除外する |
| 日本語 README 生成 | フォルダ構成・配置先・使用方法を記載した README を自動生成する |
| デプロイスクリプト生成 | PowerShell（Windows）と Bash（Linux/macOS）の再配置スクリプトを生成する |
| 元 README の更新 | 配布物の情報を元ファイルの README にも反映する |

---

## 起動パターン

```
# フックを配布する
@distribute access-control フックの配布パッケージを作成して

# エージェントを配布する
@distribute reviewer エージェントを配布用にパッケージ化して

# スキルを配布する
@distribute hooks-dev スキルの配布物を生成して

# /distribute スラッシュコマンドからも呼び出せる
/distribute access-control
```

---

## 配布物の構成

生成される配布パッケージのディレクトリ構成：

```
dist/
  <name>/
    README.md              ← 日本語README（フォルダ構成・配置手順・依存関係）
    deploy.ps1             ← 再配置スクリプト（PowerShell / Windows）
    deploy.sh              ← 再配置スクリプト（Bash / Linux・macOS）
    .github/
      hooks/
        <name>.json        ← フック設定ファイル
        config/            ← 専用設定ファイル（存在する場合）
        scripts/
          entrypoints/     ← エントリーポイント
          core/            ← コアモジュール
          shared/          ← 共有ユーティリティ
          tooling/         ← ツール入力解析
          access_control/  ← アクセス制御モジュール
```

---

## 配置先のフォルダ構成

配布パッケージを対象リポジトリに展開した場合の構成：

```
<your-repo>/
  .github/
    hooks/
      <name>.json          ← フック設定
      config/
        <name>.json        ← 専用設定（存在する場合）
      scripts/
        entrypoints/
          <name>.py        ← エントリーポイントスクリプト
        core/              ← 共有コアモジュール
        shared/            ← デバッグログ等
        tooling/           ← ツール入力解析
        access_control/    ← アクセス制御（必要な場合）
```

---

## デプロイスクリプトの使用方法

配布パッケージを受け取ったユーザーは、以下のコマンドのみで配置できます：

```powershell
# Windows / PowerShell
cd dist/<name>
.\deploy.ps1 -TargetRepo C:\path\to\your-repo
```

```bash
# Linux / macOS
cd dist/<name>
bash deploy.sh /path/to/your-repo
```

---

## テスト除外ポリシー

配布物からは以下のテスト関連コンテンツを除去します：

| 除外対象 | 内容 |
|----------|------|
| `test_*.py` | ユニットテストスクリプト |
| `testresult.md` | テスト結果記録 |
| `testcase.md` | テスト仕様書 |
| `run_tests.ps1` | テスト実行スクリプト |
| `TestHooks/` ディレクトリ | テストスイート全体 |
| Markdown のテストセクション | `## テスト作業` 等の見出し以下の節 |

**注意**: テスト機能そのものを配布したい場合（例: テストユーティリティフック）は、
エージェントにその旨を伝えることでテストファイルを含めることができます。

---

## 制約事項

- `dist/` 以外のファイルは変更しない（元 README の更新を除く）
- テスト関連ファイルは配布物に含めない（デフォルト）
- Python 標準ライブラリのみ使用するスクリプトを生成する
- 元ファイルの削除は行わない

---

## 関連ファイル

| ファイル | 役割 |
|----------|------|
| `.github/agents/distribute.agent.md` | このエージェントの定義 |
| `.github/prompts/distribute.prompt.md` | `/distribute` スラッシュコマンド |
| `.github/scripts/distribute.py` | 配布ロジック本体（Python スクリプト） |
