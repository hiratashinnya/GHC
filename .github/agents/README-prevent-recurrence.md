# prevent-recurrence エージェント / プロンプト

## 概要

ユーザーからの指摘・プロセス違反報告を受けて、原因究明から防止策実施・効果確認まで一気通貫で対応する再発防止専門ワークフローです。

## ファイル構成

| ファイル | 役割 |
|----------|------|
| `.github/prompts/prevent-recurrence.prompt.md` | ユーザーが起動するスラッシュコマンド。指摘内容を引数として受け取る |
| `.github/agents/prevent-recurrence.agent.md` | 8ステージワークフローを実行する専用エージェント |
| `.github/agents/artifact-fix.agent.md` | Stage 8 で呼び出される成果物修正専用 subagent |

## 8ステージワークフロー

| ステージ | 内容 | 出力 |
|----------|------|------|
| Stage 1 | **作業実態の確認** — git ログ・ファイル調査で事実のみを列挙 | 確認済み事実リスト |
| Stage 2 | **指摘の妥当性の検証** — 既存ルールと照合して判定 | 妥当 / 部分的に妥当 / 妥当でない |
| Stage 3 | **メリット・デメリットの検討** — トレードオフ表 | 選択肢比較表 |
| Stage 4 | **再発防止策の検討** — 対象ファイル候補と差分草案 | 候補リスト + 推奨案 |
| Stage 5 | **再発防止策の提案** — `vscode/askQuestions` ダイアログで承認（**ここで停止**） | 承認ダイアログ |
| Stage 6 | **再発防止策の実施** — 承認後に `.github/` ファイルを編集 | 変更済みファイル一覧 |
| Stage 7 | **効果確認** — 変更のロジックトレース・矛盾チェック | ✅ 効果あり / ⚠ 要修正 |
| Stage 8 | **成果物修正の委託** — Stage 1〓2で対象発見時は `artifact-fix` subagent を呼び出し修正を実施。不要な場合はスキップ | 修正結果 or 「修正不要」報告 |

## 起動方法

```
# チャットからスラッシュコマンドで起動
/prevent-recurrence テストコードを修正・実行してからtestcase.mdを更新した

# または @エージェント指定で直接起動
@prevent-recurrence テスト実施順序を守らずtestresultに「未コミット変更あり」と毎回書いていた
```

## エージェントのツール制限

| ツール | 用途 |
|--------|------|
| `read` | git ログ・`.github/` ファイルの調査 |
| `search` | 関連ルール・重複・矛盾の検索 |
| `edit` | `.github/` 配下の customization ファイルのみ編集可 |
| `execute` | `git log` 等のコマンド実行 |
| `todo` | Stage 6 の変更項目トラッキング |
| `web` | **公式ドキュメント調査専用**（VS Code docs・GitHub リリースノート等）。実装・ファイル編集目的には使用不可 |
| `vscode/askQuestions` | Stage 5 の承認ダイアログ（✅承認 / ❌却下 / 🔄修正）|
| `vscode/memory` | 再発防止策の記録・参照 |
| `agent` | Stage 8 で `artifact-fix` subagent を呼び出す |

## 制約事項

- Stage 5 でユーザーの承認を得るまで Stage 6（実施）に進まない
- このエージェント自身は `.github/` 配下のファイルのみ編集する（成果物修正は Stage 8 で `artifact-fix` に委託）
- Stage 1 では確認済み事実のみ記載し、推測を含めない
