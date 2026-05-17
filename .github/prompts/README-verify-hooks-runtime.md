# verify-hooks-runtime プロンプト README

## 概要

verify-hooks-runtime は、Hooks の実動作を一連手順で確認するためのスラッシュコマンド用プロンプトです。

確認対象は deny だけでなく、次の5観点です。

- A: ワークスペース内ファイルの作成/読取
- B: 安全な単発コマンド実行
- C: 保護パス書き込み時の confirm/ask
- D: deny ルールの実ブロック
- E: payload キー互換（snake_case / camelCase）

## 実行フロー

1. 現在ブランチ記録と stash 保存
2. 検証環境ファイルの掃除
3. test/** 形式の検証用ブランチ作成・切替
4. 観点 A-E の検証実行
5. 元ブランチ復帰と stash 自動復元

## 運用ルール

- 検証ブランチは自動削除しない
- stash は自動復元まで実施する
- stash 復元で衝突した場合は安全停止し、手動復旧手順を表示する
- 破壊的コマンドは実行しない
- テスト一括実行はユーザー明示指示がある場合のみ実施する

## 使い方

- `/verify-hooks-runtime smoke`
- `/verify-hooks-runtime full`
- `/verify-hooks-runtime rule:deny-git-force-push`

## 出力

以下を必ず出力します。

- 実行モード
- 元ブランチ名 / 検証ブランチ名
- stash 状態
- A-E 各チェックの PASS/FAIL
- deny メッセージと rule id
- 後処理状況（掃除・復元）
