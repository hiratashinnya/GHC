# stdin エンコーディング調査レポート

調査日: 2026-05-04  
対象ファイル: `.github/hooks/scripts/hook_payload.py`  
発端: `tool_input_spy.py` で `UnicodeEncodeError: surrogates not allowed` が発生

---

## 参照ドキュメント

| ドキュメント | URL |
|---|---|
| Agent hooks in Visual Studio Code (Preview) | https://code.visualstudio.com/docs/copilot/customization/hooks |
| Customize AI in Visual Studio Code | https://code.visualstudio.com/docs/copilot/customization/overview |
| AI extensibility in VS Code | https://code.visualstudio.com/api/extension-guides/ai/ai-extensibility-overview |

---

## 1. 発生したエラー

### エラーメッセージ

```
File "C:\GHC\.github\hooks\scripts\tool_input_spy.py", line 70, in main
    DEBUG.log("spy", ...)
File "C:\GHC\.github\hooks\scripts\debug_logging.py", line 54, in log
    append_debug_line(self.log_path, f"{message}{payload}")
File "C:\GHC\.github\hooks\scripts\debug_logging.py", line 32, in append_debug_line
    f.write(f"{line}\n")
UnicodeEncodeError: 'utf-8' codec can't encode character '\udcef' in position 442: surrogates not allowed
```

### エラーの発生条件

- VS Code GitHub Copilot Chat Hooks として起動（パイプ経由）
- ペイロード内に日本語（マルチバイト文字）が含まれる場合
- `tool_input_spy.py` がペイロード全体（`input_payload=payload`）を `DEBUG.log()` に渡す場合

---

## 2. 根本原因

### 伝播経路

```
VSCode（UTF-8でペイロード送信）
  → パイプ → Python プロセス
               └─ sys.stdin.read()        ← cp932 で UTF-8 バイト列を読む
                    └─ json.loads()       ← \udcef 等のサロゲート文字が混入した dict が生成される
                         └─ json.dumps()  ← サロゲート文字を含む str を返す
                              └─ f.write(encoding="utf-8")  ← UTF-8 はサロゲート文字を表現できない
                                   └─ UnicodeEncodeError: surrogates not allowed
```

### 原因の詳細

Python で `sys.stdin.read()` を使うと、**テキスト層（`sys.stdin`）** のエンコーディングが使われる。

| 実行環境 | `sys.stdin.encoding` | 結果 |
|---|---|---|
| TTY（ターミナル直接起動） | `utf-8` | 正常 |
| パイプ（hook として起動） | `cp932`（日本語 Windows） | 異常 |

hook として起動される場合（非TTY）は `locale.getpreferredencoding()` の値である `cp932` が採用される。VS Code は常に UTF-8 でペイロードを送信するため、`cp932` で読むと解釈できないバイト（例: UTF-8 の `0xEF`）が **サロゲートエスケープ文字（`\udcef` 等）** に変換される。

`json.dumps()` はサロゲート文字をそのまま str に含めて返し、`f.write(encoding="utf-8")` の段階で UTF-8 がサロゲート文字（U+DC00〜U+DFFF）を表現できないため `UnicodeEncodeError` が発生する。

### なぜ `tool_input_spy.py` だけで発生したか

他のスクリプトは `tool_name` や `keys` 等の**安全なフィールドのみ** を `DEBUG.log()` に渡しているが、`tool_input_spy.py` だけが `input_payload=payload`（**ペイロード全体**）を渡していたため、サロゲート文字を含む `tool_input` の値まで `json.dumps` / `f.write` を通過した。

---

## 3. 修正内容

### 対象ファイル

`hook_payload.py` の `read_payload()` 関数

### 変更箇所

```python
# 修正前
raw = sys.stdin.read().strip()

# 修正後
raw = sys.stdin.buffer.read().decode("utf-8").strip()
```

### 修正の原理

`sys.stdin.buffer` は Python のテキスト層を**バイパス**した生バイト列ストリームである。

```
sys.stdin         (テキスト層)  … エンコーディング設定に左右される
sys.stdin.buffer  (バイト層)   … エンコーディングなし。生バイトをそのまま返す
```

`sys.stdin.buffer.read()` で取得したバイト列を `.decode("utf-8")` で明示的にデコードすることにより、OS のロケール設定や Python のエンコーディング設定に関わらず常に正しく UTF-8 デコードされる。

---

## 4. 環境変数による制御の調査

### Q. VSCode 側の設定でエンコーディングを変更できるか

**不可。** VS Code hooks の公式ドキュメントには stdin エンコーディングを制御する設定項目は存在しない。

ただし hook JSON の `env` プロパティを使って Python 側のエンコーディングを制御することは可能：

```json
{
  "type": "command",
  "command": "python .github/hooks/scripts/entrypoints/tool_input_spy.py",
  "env": {
    "PYTHONUTF8": "1"
  }
}
```

これは修正**前**の `sys.stdin.read()` を使う場合の**別の修正案**である。今回の修正（`sys.stdin.buffer`）とは対象レイヤーが異なる。

### Q. 実行時にエンコーディングを環境変数等で判別できるか

**可能。** 以下の手段が利用できる：

| 手段 | 取得方法 | 用途 |
|---|---|---|
| `sys.stdin.encoding` | `sys.stdin.encoding` | 現在の stdin エンコーディング確認 |
| `PYTHONUTF8` | `os.environ.get('PYTHONUTF8')` | Python UTF-8 モードが有効か |
| `PYTHONIOENCODING` | `os.environ.get('PYTHONIOENCODING')` | I/O エンコーディング強制指定 |
| `locale.getpreferredencoding()` | `locale.getpreferredencoding()` | システムロケールの優先エンコーディング |

### 確認環境での値（日本語 Windows）

```
sys.stdin.encoding       : utf-8         ← TTY 接続時（ターミナルから確認）
locale.getpreferredencoding : cp932      ← パイプ接続時（hook として起動時）に採用される値
PYTHONUTF8               : (not set)
PYTHONIOENCODING         : (not set)
```

---

## 5. 今回の修正がエンコーディング設定に依存しない理由

`sys.stdin.buffer` はテキスト層を通らないため、以下のいずれの条件下でも動作が変わらない：

| 条件 | `sys.stdin.read()` (旧) | `sys.stdin.buffer.read().decode("utf-8")` (新) |
|---|---|---|
| `PYTHONUTF8` 未設定 | cp932 で読む → エラー | 影響なし |
| `PYTHONUTF8=1` 設定 | utf-8 で読む → 正常 | 影響なし |
| `PYTHONIOENCODING=utf-8` 設定 | utf-8 で読む → 正常 | 影響なし |
| TTY 接続（ターミナル起動） | utf-8 → 正常 | 影響なし |
| パイプ接続（hook として起動） | cp932 → **エラー** | 影響なし |

修正後の動作は「VS Code が UTF-8 で送る → `buffer.read()` でバイト列取得 → `.decode("utf-8")` で常に正しくデコード」という**固定フロー**であり、環境変数・ロケール設定に関わらずエラーは再発しない。

---

## 6. 「VS Code が UTF-8 で送る」保証の有無

### 結論

**明文化された保証はない。** VS Code の hooks 公式ドキュメントは「stdin で JSON オブジェクトを受け取る」と仕様を記述しているが、エンコーディングを UTF-8 と明記した記述は存在しない。

### 実質的な根拠（保証ではなく前提）

| 根拠 | 説明 |
|---|---|
| RFC 8259 §8.1 | 「システム間で交換される JSON テキストは UTF-8 でエンコードしなければならない（MUST）」と規定 |
| VS Code が Node.js 製 | Node.js は子プロセスの stdin パイプに書き込む際、文字列を UTF-8 でエンコードする（`Buffer.from(str)` のデフォルト） |
| 実際の動作確認 | 今回のエラーログが示すとおり、UTF-8 として解釈すれば正しく動作する |

### 仮定が崩れた場合の失敗モード比較

`sys.stdin.buffer.read().decode("utf-8")` の弱点は「VS Code が UTF-8 以外で送るようになった場合に `UnicodeDecodeError` で即クラッシュする」ことである。ただしこれは現状より**望ましい失敗モード**である。

| | 旧: `sys.stdin.read()` | 新: `.buffer.read().decode("utf-8")` |
|---|---|---|
| UTF-8 ペイロード | cp932 環境でサイレント誤変換 → ログ書き込み時にクラッシュ | 正常 |
| UTF-8 以外のペイロード | サイレント誤変換（気づけない） | **即クラッシュ**（気づける） |

旧コードはエンコーディングが違っても気づかずに誤ったデータをログに記録し続ける。新コードは仮定が崩れた瞬間に明示的に失敗するため、問題の検出が容易である。

### より堅牢にする選択肢（将来の検討事項）

将来の仕様変更に備えるなら `errors="replace"` を加えてクラッシュを防ぐことも可能：

```python
raw = sys.stdin.buffer.read().decode("utf-8", errors="replace").strip()
```

ただしこれは「文字化けしてもログを残す」トレードオフであり、今回の修正範囲外。

