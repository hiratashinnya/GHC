# 新規フック作成 — チェックリストとテンプレート

新しいフックスクリプト（`.py`）を作成する際のチェックリストと Python テンプレート。
`copilot-instructions.md` のデバッグ要件を満たすために全項目を確認すること。

---

## チェックリスト

### 基本構造

- [ ] `debug_logging.HookDebugLogger` をインポートして `DEBUG = HookDebugLogger(SCRIPT_DIR, "<script_name>")` を初期化
- [ ] デバッグフラグファイルは `<script_name>.debug`（スクリプトと同じディレクトリ）
- [ ] ログファイルは `<script_name>.debug.log`（自動生成）

### デバッグログ

- [ ] 入力受信時に `DEBUG.log("input", ...)` を記録（tool_name, keys 等）
- [ ] 出力・処理結果を `DEBUG.log("done", ...)` で記録
- [ ] 例外・エラー時も `DEBUG.log("error", ...)` で記録

### 出力制御

- [ ] `from hook_output import HookOutput` をインポートし、`OUT = HookOutput(payload.get("hookEventName", "<EventName>"))` を初期化
- [ ] 出力後は必ず `sys.exit(code)` を呼ぶ（`sys.exit(OUT.method(...))` の形で1行にまとめ可）
- [ ] **ブロックも警告も不要な場合**: 何も呼ばずに `return`（stdout に何も書かない）
- [ ] **ツール単体をブロック（理由なし）**: `sys.exit(OUT.block("stderr メッセージ"))`
- [ ] **PreToolUse でユーザーに理由を表示してブロック**: `sys.exit(OUT.deny("理由"))`
- [ ] **ユーザー承認が必要な場合**: `sys.exit(OUT.ask("理由"))`（VS Code のみ対応）
- [ ] **警告を表示したい場合**: `sys.exit(OUT.warn("メッセージ"))`
- [ ] **セッション全体を停止する場合**: `sys.exit(OUT.stop_session("理由"))`
- [ ] **PostToolUse でブロック**: `sys.exit(OUT.block_post("理由"))`
- [ ] **コンテキストを注入**: `sys.exit(OUT.add_context("テキスト"))`
- [ ] **ツール入力を変更（PreToolUse）**: `sys.exit(OUT.update_input(new_input_dict))`

### セキュリティ

- [ ] `tool_input` の値は必ずバリデーションしてから使用する
- [ ] ログにシークレット・パスワード・APIキーを記録しない
- [ ] プロンプトのログを記録する場合はマスキングを施す

---

## Python テンプレート（最小版）

テンプレートファイル: [.github/hooks/scripts/hook-template.py](../hooks/scripts/hook-template.py)
出力制御ライブラリ: [.github/hooks/scripts/hook_output.py](../hooks/scripts/hook_output.py)

新しいスクリプトを作成する際は `hook-template.py` をコピーして使用すること。
出力制御は `HookOutput` クラスのみを使う。`print(json.dumps(...))` や `sys.exit(2)` を直接書かないこと。

> **stdout 出力の原則**: ブロックも警告も不要な場合は何も呼ばずに `return` する。
> `sys.exit(OUT.method(...))` を呼ぶのは何らかの出力・制御が必要な場合のみ。

---

## ブロック実装パターン集

### パターン A: ツール単体ブロック（exit code 2 のみ）

最もシンプル。`stderr` の内容がモデルへのコンテキストとして渡される。

```python
sys.exit(OUT.block("危険なコマンドをブロックしました"))
```

### パターン B: ツール単体ブロック（permissionDecision deny）

ユーザーにわかりやすい理由を表示したい場合。

```python
sys.exit(OUT.deny("本番ファイルへの直接書き込みは禁止されています"))
```

### パターン C: ユーザー承認要求（ask）

ユーザーに確認ダイアログを表示して承認/拒否させる（VS Code のみ）。

```python
sys.exit(OUT.ask("本番環境に影響する操作です。実行しますか？"))
```

### パターン D: セッション全体の停止

ツール1回ではなく、セッションそのものを終わらせる際に使用（使用は慎重に）。

```python
sys.exit(OUT.stop_session("セキュリティポリシー違反が検出されたためセッションを終了します"))
```

### パターン E: 警告メッセージ（続行しつつ通知）

処理は続けるが、ユーザーにチャットで警告メッセージを表示する。

```python
sys.exit(OUT.warn("⚠️ 本番ファイルを編集しています。注意してください。"))
```

> **原則**: ブロックも警告も不要な場合は何も呼ばずに `return` するだけ。`sys.exit(OUT.method(...))` を呼ぶのは何らかの出力・制御が必要な場合のみ。

---

## hook JSON 設定テンプレート

`.github/hooks/<name>.json` に配置する設定ファイルのテンプレート。

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "type": "command",
        "command": "python .github/hooks/scripts/<script_name>.py",
        "windows": "python .github/hooks/scripts/<script_name>.py",
        "cwd": ".",
        "timeout": 15
      }
    ],
    "PostToolUse": [
      {
        "type": "command",
        "command": "python .github/hooks/scripts/<script_name>.py",
        "cwd": ".",
        "timeout": 30
      }
    ]
  }
}
```

> `version: 1` は VS Code フォーマットでは**不要**（Copilot CLI/Cloud Agent フォーマットでは必要）。
> VS Code の hook 設定は `hooks` オブジェクトのみが必須。
