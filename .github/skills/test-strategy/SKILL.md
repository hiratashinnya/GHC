---
name: test-strategy
description: "Use when planning how to test the implementation — unittest per public function, Markdown test cases, commit-before-test workflow, e2e with same 3-set. Tool-specific knobs (module scope, non-determinism seam, e2e scenario) are fixed per tool via DD#. Trigger phrases: test strategy, testing plan, how to test, test approach, TDD, test planning."
---

# テスト戦略（GHC テーラリング済・active）

> 汎用標準 [`.claude/standards/test-strategy`](../../../.claude/standards/test-strategy/SKILL.md) の**不変条件を継承**し、本PJのノブを埋めた版。
> 由来・差分は [tailoring-registry](../../../.claude/tailoring-registry.md)。

## 継承する不変条件（標準のまま）
unittest 基本／ケース＝Markdown／成績書＝ケースコピー＋実測＋commit id／ログ＝標準出力ダンプをリンク／
失敗も残す（隠蔽・上書き禁止＋原因/対策）／e2e も同じ3点セット／**テスト前にコミット**。3点セットの対応を保つ。

## 本PJのノブ（埋めた値）

| ノブ | GHCの決定 |
|---|---|
| 「1関数」の定義・網羅 | **tool固有 → 各ツール開発時にDD#で確定**。現行例(hooks-infra): `.github/hooks/scripts/` の全 public 関数 |
| 非決定の決定化シーム | **tool固有 → 各ツール開発時にDD#で確定**。現行(hooks-infra): stdin payload = 決定的なため不要。LLM使用ツールは依存ポート境界でFake化（DD#） |
| e2e の駆動・対象 | **tool固有 → 各ツール開発時にDD#で確定**。現行例: stdin payload直接注入 + `python entrypoints/<hook>.py` |
| ログ取得 | `python -m unittest -v` 出力を testresult.md にインライン記録（基本）。複雑シナリオは `tee <tool>-<commit>.txt` をDD#で追加 |
| ディレクトリ配置 | `TestHooks/<tool>/test_<tool>.py`（ユニット）・`TestHooks/<tool>/testcase.md`（ケース）・`TestHooks/<tool>/testresult.md`（成績書） |
| バージョニング | 成績書ヘッダに `{ 実行日 + コミットID + 実行コマンド + 総合結果 }`（基本）。LLMツールは `+ 雛形版 + content_hash` をDD#で追加 |
| 実行ランナー | **`python -m unittest`**（標準ライブラリのみ・Q5） |

## 3点セットのテンプレ（本PJ）

**ケース** `TestHooks/<tool>/testcase.md`
```
# testcase: <tool>

対象スクリプト: `<path>`
関連モジュール: `<modules>`

---

## テストケース一覧

| テストID | 観点 | 入力 | 期待動作 |
|----------|------|------|----------|
| XX-001   | ...  | ...  | ...      |
```

**成績書** `TestHooks/<tool>/testresult.md`
```
# testresult: <tool>

対象スクリプト: `<path>`
実行日: YYYY-MM-DD
コミットID: <commit>
実行コマンド: `cd TestHooks/<tool> && python -m unittest test_<tool> -v`
総合結果: PASS|FAIL (<passed>/<total>)

---

## テスト結果

| テストID | クラス | 観点 | 結果 | 判定 |
|----------|--------|------|------|------|

（FAIL時）
## 失敗ケース — 原因調査・対策検討  ← 隠蔽・上書き禁止（PR8）
```

**ユニットテスト** `TestHooks/<tool>/test_<tool>.py` … `python -m unittest` で実行可能な形式。

## 手順（1サイクル）
1. 実装を**コミット**（commit id を確定）。
2. `cd TestHooks/<tool> && python -m unittest test_<tool> -v`。
3. testresult.md にヘッダ（実行日/コミットID/実行コマンド/総合結果）＋テスト結果表を記録。
4. FAIL は成績書をそのまま残し、原因調査・対策検討を併記（消さない・上書きしない）。
5. e2e は tool固有シナリオをDD#で定義し、同じ3点セット形式で記録。
