# Customization Verification Perspectives

## 対象

`.github/` 配下の全カスタマイゼーションファイル（`agents/*.agent.md`, `skills/*/SKILL.md`, `prompts/*.prompt.md`, `instructions/*.instructions.md`, `copilot-instructions.md`）

## 使用方法

`adversarial.agent.md` の Stage V2 において、各観点を **1観点 = 1 `perspective-checker` サブエージェント呼び出し** で実行する。各呼び出しは独立コンテキストなので、他の観点の結果を参照しない。

---

## 観点リスト

### P-CUS-01: YAML フロントマター構文・必須フィールド

**観点の目的**: フロントマターの形式的正しさを検証する。

**チェック項目**:
- `---` ブロックが正しく開閉されているか（先頭 `---`、末尾 `---`）
- `name` フィールドが存在するか
- `description` フィールドが存在するか、かつ「Use when」形式のトリガーワードを含むか
- コロンを含む `description` が引用符で囲まれているか
- `tools` フィールドが存在する場合、配列形式か（例: `[read, search]`）
- `agents` フィールドが存在する場合、配列形式か

**判定基準**:
- フィールド欠如・`---` 未閉鎖・引用符漏れ → **Lv1**（機械的に修正可能）
- `description` にトリガーワードがない・曖昧（Use when 形式でない）→ **Lv2**

---

### P-CUS-02: name とファイル名の整合性

**観点の目的**: `name` 値がファイル命名規約に従っているか検証する。

**チェック項目**:
- `.agent.md` の場合: `name` がファイル名（`.agent.md` を除いた部分）と一致するか
- `SKILL.md` の場合: `name` がスキル格納フォルダ名と一致するか
- `.prompt.md` の場合: `name` がファイル名（`.prompt.md` を除いた部分）と一致するか
- `.instructions.md` の場合: `name` が存在する場合、ファイル名と一致するか

**判定基準**:
- 不一致 → **Lv1**（機械的に修正可能）

---

### P-CUS-03: ツール制約・言語制約

**観点の目的**: 禁止ツール・禁止言語・禁止パッケージの使用がないか検証する。

**チェック項目（`copilot-instructions.md` の「言語・ツール制約」との照合）**:
- Python スクリプト内に非標準ライブラリ（`pip install` が必要なモジュール）のインポートがないか
  - 禁止例: `import requests`, `import numpy`, `import pandas`, `import yaml`（非標準）
  - 許可例: `import os`, `import sys`, `import json`, `import re`, `import pathlib`
- PowerShell スクリプト内に外部モジュール（`Install-Module` で取得するもの）の使用がないか
- `tools` フィールドに不必要なツールが含まれていないか（**swiss-army anti-pattern**: 無関係なツールを全部列挙）
- Markdown / YAML 以外の設定言語が禁止されていないか

**判定基準**:
- 禁止ライブラリの明示的インポート → **Lv1**（禁止ライブラリが特定できる場合）
- `tools` 過多（5種超で役割に不要なツールを含む）→ **Lv2**
- 言語制約の曖昧な違反（グレーゾーン）→ **Lv2**

---

### P-CUS-04: 既存ファイルとの重複・矛盾

**観点の目的**: 同等の役割を持つ既存ファイルや矛盾するルールがないか検証する。

**チェック項目**:
- 名前・目的が重複する既存ファイルが `.github/` 配下に存在しないか（`search` ツールで確認）
- `copilot-instructions.md` の順守事項と矛盾する制約・方針がないか
- 同一エージェント名・スキル名が複数ファイルに定義されていないか
- 既存のエージェントや skill が持つ責務と役割が大幅に重複していないか

**判定基準**:
- 完全重複（同一名・同一目的のファイルが既存）→ **Lv1**（削除または統合）
- 部分的重複・役割の曖昧な重なり → **Lv2**
- 方針レベルの矛盾（どちらを優先するか判断が必要）→ **Lv3**

---

### P-CUS-05: Anti-pattern チェック

**観点の目的**: Copilot カスタマイゼーションの既知の悪習慣（アンチパターン）を検出する。

**チェック項目**:
- **Agent**: `tools` が過多で汎用化しすぎていないか（swiss-army agent — 何でもできる万能エージェント）
- **Agent**: `description` が「何でもする」「全般的に」「あらゆる」系の表現になっていないか
- **Agent**: `user-invocable: false` が必要なサブエージェントに対してフラグが設定されているか
- **Skill**: `SKILL.md` の本文に具体的な手順（ステップ形式・番号付き手順等）が記載されているか
- **Skill**: 観点・概念のみで実際の手順がない抽象的な記述になっていないか
- **Prompt**: 単一ファイルに複数の無関係タスクが詰め込まれていないか
- **Instructions**: `applyTo` パターンが広すぎてワークスペース全体のパフォーマンスに影響しないか

**判定基準**:
- Swiss-army pattern（`tools` 7種超 + `description` が汎用的）→ **Lv2**
- Skill 本文に手順がない（概念説明のみ）→ **Lv2**
- Prompt に複数の独立タスク → **Lv2**
- `applyTo: "**"` で巨大ワークスペース（判断が必要）→ **Lv3**
