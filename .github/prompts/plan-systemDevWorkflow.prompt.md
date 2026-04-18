# システム開発ワークフロー設計

## 概要

全SDLC（6フェーズ）を対象に、各フェーズ内で①〜⑤の5プロセスに分割する。
フェーズ間はYAMLフロントマター付きMarkdownで厳格にI/Oを規格化し、
③意思決定と⑤検証の2点を人間のゲートとする。

**基本方針:**
- **イテレーション**: 大規模要求はフェーズ2以降を複数回イテレーションに分割して進める
- **フェーズゲート**: `PreToolUse` フックで `approval-required: true` かつ `status: approved` でないドキュメントを機械的にブロック
- **TDD**: 詳細設計フェーズでテストケースを先行設計し、実装フェーズでは Red→Green→Refactor サイクルで進める
- **正本と差分**: `docs/` は常にプロジェクトの最新正本を保持する。各フェーズの変更点は `iter/iterN/phaseX/` 配下の差分ドキュメントに記載し、承認後に正本へマージする
- **ダッシュボード**: `docs/dashboard.md` で全フェーズ・プロセスのステータスをリアルタイム可視化する。フックで自動更新され、作業着手前に必ず最新状態とする
- **ダイアグラム**: 依存関係図・ER図・フロー図等のビジュアル要素は Mermaid または PlantUML で記述する。矢印記号（`→`, `─`, `│` 等）によるテキストアート表現は禁止する
- **リスクID**: 未解決事項・リスクは `RISK-{phase略称}-NNN` 形式で統一する（例: `RISK-REQ-001`, `RISK-DD-001`）。セクション名は全フェーズ共通で「未解決事項・リスク」とする
- **差し戻しルーティング**: ①入力検証・⑤成果物検証でNG時の差し戻し先判定は `routing-on-failure` スキルで定義する
- **ダッシュボード確認/更新スキル**: フェーズごとのダッシュボード確認・更新手順は `dashboard-sync-{phase}` スキルとして切り出し、オーケストレータが参照する

---

## フェーズ一覧と①〜⑤の適用方針

> **実装状況**: ✅ 設計完了 — テンプレート・ディレクトリ構成に反映済み


| # | フェーズ | ④の主成果物 | ③人間ゲート内容 | ⑤人間ゲート内容 |
|---|---------|------------|----------------|----------------|
| 1 | 要件定義 | PRD（要求仕様書） | 要求優先度・スコープ境界 | PRD完全性承認 |
| 2 | 基本設計 | アーキテクチャ設計書 | アーキテクチャ方式選択 | 設計の要件カバレッジ承認 |
| 3 | 詳細設計 | API仕様・DBスキーマ・**テストケース設計**（3層分割） | 設計パターン・アルゴリズム選択・テスト戦略 | 実装可能性・整合性・テストケース網羅性承認 |
| 4 | 実装（TDD） | テストコード先行 → プロダクションコード | 実装順序・リファクタリング方針 | コードレビュー・全テストグリーン承認 |
| 5 | テスト | 統合・E2Eテスト報告書 | カバレッジ目標・品質基準確認 | 品質基準達成の承認 |
| 6 | リリース | リリースノート・デプロイ完了 | リリース方式・タイミング | スモークテスト・監視確認 |

**フレキシビリティ注記:**
- フェーズ2+3は小規模プロジェクトでは統合可能
- フェーズ3（詳細設計）の②③④はコンポーネント単位にファイル分割する（後述「詳細設計フェーズの分割構造」参照）
- フェーズ4の「②分解」はコーディングタスク（チケット）リストを産出
- フェーズ5の「④成果物」はAIが実行してレポートを生成（手作業不要）
- フェーズ6の「④成果物」はデプロイ実行そのものも含む

---

## イテレーション方針

> **実装状況**: ✅ 設計完了 — オーケストレータの委譲ルールおよびディレクトリ構成（`iter/`）に反映済み。フック実装は未着手（⏸）


大規模要求（スコープが広い・複数サブシステムにまたがる等）はフェーズ2以降を**複数イテレーション**に分割する。

```
Iteration 1: フェーズ2 → 6（コアMVP相当）
Iteration 2: フェーズ2 → 6（追加機能セット A）
Iteration 3: フェーズ2 → 6（追加機能セット B）
...
```

- フェーズ1（要件定義）は全イテレーション共通で1回のみ実施（優先度付け・スコープ分割を含む）
- 各イテレーションの差分ドキュメントは `iter/iterN/phaseX/` 配下に配置する
- イテレーション境界は `docs/requirements/03-decisions.md` でスコープ分割を決定し、人間が承認する

---

## フェーズゲート強制（フック）

> **実装状況**: 🚧 一部実装 — オーケストレータのフェーズゲートチェック（ソフト強制）は完了。`PreToolUse` フックによる機械的ブロックは**未実装**（⏸ フック作成フェーズで対応）


フェーズ・プロセスのゲートは **`PreToolUse` フックで機械的にブロック**する。

- ③（`03-decisions.md`）と⑤（`05-verification.md`）は `approval-required: true` を付与する
- `approval-required: true` かつ `status: approved` でないドキュメントが存在する場合、次プロセスへの移行をフックがブロックする
- ブロック時はエラーメッセージに未承認ドキュメントのパスとステータスを明示する

```
PreToolUse hook（成果物作成・ファイル書き込み前）:
  → 前プロセスの approval-required: true doc を走査
  → status != "approved" なら実行をブロックしエラー出力
```

---

## 正本と差分ドキュメント

> **実装状況**: ✅ 設計完了 — 差分テンプレート（`.github/templates/diff-document.md`）・正本ディレクトリ（`docs/<phase>/`）・差分ディレクトリ（`iter/`）を作成済み。マージ手順はオーケストレータに組み込み済み


継続開発を想定し、ドキュメントを2種類に分類する。

| 種別 | 配置先 | 内容 |
|------|--------|------|
| **正本** | `docs/<phase>/` | プロジェクトの実態を表す常時最新の公式ドキュメント |
| **差分** | `iter/iterN/phaseX/` | 当該イテレーション・フェーズの要求/変更点のみを記載 |

**マージルール:**
1. 各プロセスはまず差分ドキュメント（`iter/iterN/phaseX/`）を作成する
2. 差分ドキュメントが `status: approved` になったら `docs/<phase>/` の正本へマージする
3. 次プロセスへ進む前に、正本・差分ドキュメント双方が最新状態であることを確認する
4. マージ後の正本は `version` をインクリメントし `updated-at` を更新する

**差分ドキュメントの追加フロントマターフィールド:**
```yaml
doc-kind: diff           # diff | master を明示
iteration: 1             # イテレーション番号
base-version: "1.2"      # マージ元となる正本のバージョン
```

---

## I/O フォーマット規格

> **実装状況**: ✅ 設計完了 — 全テンプレートファイル（`.github/templates/0N-*.md`）にフロントマター反映済み


各プロセスの出力ドキュメントに**共通YAMLフロントマター**を付与する：

```yaml
---
doc-type: validation | breakdown | decision | artifact | verification
doc-kind: diff | master
phase: requirements | basic-design | detailed-design | implementation | testing | release
process: 1 | 2 | 3 | 4 | 5
iteration: 1             # イテレーション番号（要件定義は 0 固定）
version: "1.0"
status: draft | awaiting-approval | approved | rejected
input-refs:
  - path: "../requirements/artifact.md"
    version: "1.0"
created-at: "YYYY-MM-DD"
updated-at: "YYYY-MM-DD"
approved-by: null        # 人間ゲート時のみ記入
approved-at: "YYYY-MM-DD"        # 承認時に自動記載（YYYY-MM-DD HH:MM）。approval-required: true のドキュメントのみ
approval-required: false # true の場合は次プロセスへ進行不可
---
```

**`approved-at` フィールドについて:**
- `approval-required: true` のドキュメント（`03-decisions.md`, `05-verification.md`）に付与する
- `status` が `approved` に変更される際、フックまたはオーケストレータが `approved-at` を現在日時で自動記載する
- 監査証跡として承認のタイムスタンプを保持する

---

## ドキュメントツリー

> **実装状況**: ✅ 実体化済み — `docs/<phase>/`・`iter/`・`src/` ディレクトリを `.gitkeep` で作成済み, 一部未実装


```
docs/                              # 正本ツリー（常時最新の公式ドキュメント）
  dashboard.md                     # プロジェクト全体ダッシュボード
  requirements/
    01-validation.md               # ① 入力検証レポート
    02-breakdown.md                # ② 機能/非機能/制約/スコープ外の分解
    03-decisions.md                # ③ 優先度・スコープ決定（human gate）
    04-artifact.md                 # ④ PRD概要 + イテレーションファイルへのリンク
    iterations/
      04-artifact-iter1.md         # ④ iter1スコープ詳細
      04-artifact-iter2.md         # ④ iter2スコープ詳細（以降同様）
    05-verification.md             # ⑤ PRD検証・承認（human gate）
  basic-design/
    01-validation.md
    02-breakdown.md
    03-decisions.md                # ③ アーキテクチャ方式選択（human gate）
    04-artifact.md                 # ④ アーキテクチャ設計書
    05-verification.md
  detailed-design/
    01-validation.md
    02-breakdown-overview.md       # ② 全体分解（コンポーネント配分・トレーサビリティ）
    02-breakdown-validation.md     # ②v 分解の妥当性検証（サブプロセス）
    03-decisions-overview.md       # ③ 全体サマリ（意思決定一覧）
    components/                    # ③④ コンポーネント別詳細
      {compId}/                    # ④ 設計項目別ファイル
        02-breakdown-{compId}.md   # ② コンポーネント単位の詳細分解
        03-decisions-{compId}.md   # ③ コンポーネント別意思決定
        04-artifact-{compId}.md    # ④ コンポーネント別設計書サマリ
        04-artifact-{compId}-api.md
        04-artifact-{compId}-schema.md
        04-artifact-{compId}-domain.md
        04-artifact-{compId}-testcase.md
        05-verification-{compId}.md    # ⑤ 詳細設計検証・承認
    04-artifact-overview.md            # ④ 全体サマリ（コンポーネント横断）
    05-verification-overview.md        # ⑤ 詳細設計検証・承認
  implementation/
    01-validation.md
    02-breakdown.md                # ② コーディングタスクリスト
    03-decisions.md
    04-artifact.md                 # ④ タスク完了サマリ + src/ への参照リスト
    05-verification.md
  testing/
    01-validation.md
    02-breakdown.md
    03-decisions.md
    04-artifact.md                 # ④ 統合・E2Eテスト報告書
    05-verification.md
  release/
    01-validation.md
    02-breakdown.md
    03-decisions.md
    04-artifact.md                 # ④ リリースノート
    05-verification.md

iter/                              # 差分ドキュメントツリー（docsツリー外）
  iter1/
    phase2/                        # basic-design の差分（同構造）
    phase3/
    phase4/
    phase5/
    phase6/
  iter2/
    ...                            # 同構造

src/                               # プロダクションコード（docsツリー外）
```

---

## TDDフロー

> **実装状況**: ✅ 設計完了 — `04-artifact.md` テンプレートのテストケース設計セクション・オーケストレータのフロー説明に反映済み。実装エージェント（`implementation-agent`）は未作成（⏸）


実装フェーズはテスト駆動開発（TDD）で進める。詳細設計フェーズで**先行テストケース設計**を行い、実装フェーズで **Red→Green→Refactor** サイクルを繰り返す。

```mermaid
graph TD
    DD4[\"フェーズ3: 詳細設計 ④成果物<br/>API仕様 + DBスキーマ + テストケース設計書\"]
    DD5{\"フェーズ3: ⑤ approved?\"}
    IMP2[\"フェーズ4: ② コーディングタスクリスト作成\"]
    IMP3{\"フェーズ4: ③ 実装順序・Refactor方針<br/>人間承認\"}
    TDD[\"フェーズ4: ④ TDDサイクル<br/>Red → Green → Refactor\"]
    IMP5{\"フェーズ4: ⑤ 全テストグリーン<br/>+ コードレビュー承認\"}
    TST4[\"フェーズ5: ④ 統合テスト・E2Eテスト<br/>→ 報告書生成\"]

    DD4 --> DD5
    DD5 -->|approved| IMP2
    IMP2 --> IMP3
    IMP3 -->|approved| TDD
    TDD --> IMP5
    IMP5 -->|approved| TST4
```

**実装フェーズの④成果物について:**
- コード本体は `src/` 以下に配置する（docsツリーには含めない）
- `docs/implementation/04-artifact.md` はコーディングタスク完了サマリと `src/` への参照リストのみを記載する

---

## 要件定義フェーズの成果物分割

> **実装状況**: ✅ 設計完了 — `04-artifact.md` を概要版に修正、`04-artifact-iterN.md` テンプレート作成済み

`requirements/04-artifact.md`（PRD）のイテレーション別スコープは、イテレーションごとにファイルを分割する。

```
docs/requirements/
  04-artifact.md               # PRD概要（プロジェクト概要・全体スコープ・共通事項）
  iterations/
      04-artifact-iter1.md         #  iter1スコープ詳細（機能要件・US・受入基準）
      04-artifact-iter2.md         #  iter2スコープ詳細（以降同様）
      ...
```

- `04-artifact.md` 本体にはプロジェクト概要・非機能要件・制約条件・用語定義と、各イテレーションファイルへのリンク一覧のみ記載する
- 各イテレーションファイル（`iterations/04-artifact-iterN.md`）には当該イテレーションの機能要件・ユーザーストーリー・受入基準を記載する
- `input-refs` は各イテレーションファイルが親の `04-artifact.md` を参照する

---

## 詳細設計フェーズの分割構造

> **実装状況**: ✅ 設計完了 — 3層分割テンプレート13ファイル作成済み。旧モノリシックテンプレート（02/03/04/05）を削除済み

詳細設計フェーズは成果物の粒度が大きいため、**3層構造**でファイルを分割する。コンポーネントIDは `basic-design/04-artifact.md` の `COMP-ID` を起点とするが、詳細設計で独自にサブコンポーネントへ再分割できる。

### 3層構造

| 層 | ファイル例 | 内容 |
|----|----------|------|
| L1: 全体サマリ | `03-decisions-overview.md`, `04-artifact-overview.md` | 全コンポーネント横断のサマリ・方針 |
| L2: コンポーネントサマリ | `components/{compId}/04-artifact-{compId}.md` | コンポーネント単位の設計サマリ |
| L3: 設計項目 | `components/{compId}/04-artifact-{compId}-api.md` | API/スキーマ/ドメインモデル/テストケース等 |

下記のようにディレクトリ・ファイル構成を整理する：
```
docs/detailed-design/
    02-breakdown-overview.md                # ② 全体分解（コンポーネント配分・トレーサビリティ）
    02-breakdown-validation.md              # ②v 分解の妥当性検証（サブプロセス）
    03-decisions-overview.md                # 全体の意思決定サマリ
    components/                             # ③④ コンポーネント別詳細
      {compId}/                             # ④ 設計項目別ファイル
        02-breakdown-{compId}.md            # ② コンポーネント単位の詳細分解
        04-artifact-{compId}.md             # ④ コンポーネント別設計書サマリ
        04-artifact-{compId}-api.md
        04-artifact-{compId}-schema.md
        04-artifact-{compId}-domain.md
        04-artifact-{compId}-testcase.md
```
### ②分解プロセスの拡張

②分解プロセスを3サブプロセスに分割する:

| サブプロセス | ファイル | 内容 |
|------------|---------|------|
| ②-a 全体分解 | `02-breakdown-overview.md` | basic-design → コンポーネント配分マッピング（COMP-ID紐付け） |
| ②-b コンポーネント分解 | `components/{compId}/02-breakdown-{compId}.md` | コンポーネント単位のAPI/テーブル/テストケース分解 |
| ②-v 分解検証 | `02-breakdown-validation.md` | 分解の妥当性・抜け漏れ検証（サブプロセス） |

**②-a `02-breakdown-overview.md` のトレーサビリティ:**
- 各分解要素（API, テーブル, テストケース等）にコンポーネントIDを紐付ける
- `COMP-ID → [API-xxx, TBL-xxx, TC-xxx]` の配分マトリクスを記載する
- basic-designのコンポーネント仕様との整合性を担保する

**②-v `02-breakdown-validation.md` の検証観点:**
- basic-designの全コンポーネントが②-aで配分されているか（漏れ検証）
- 各コンポーネントの②-b分解がMECEか（重複・不足検証）
- 要件IDとのトレーサビリティが維持されているか
- このサブプロセスでNG判定の場合、②-a/②-bへ差し戻す

### ③意思決定・④成果物の分割

③意思決定と④成果物は全体サマリ + コンポーネント別ファイルに分割する:

```
docs/detailed-design/
  03-decisions-overview.md                     # 全体の意思決定サマリ
  components/
    {compId}/
      03-decisions-{compId}.md                 # コンポーネント別意思決定
      04-artifact-{compId}.md                  # コンポーネント別設計サマリ
      04-artifact-{compId}-api.md              # API仕様
      04-artifact-{compId}-schema.md           # DBスキーマ
      04-artifact-{compId}-domain.md           # ドメインモデル・DTO定義
      04-artifact-{compId}-testcase.md         # テストケース設計
  04-artifact-overview.md                      # 全体の設計サマリ（横断的事項）
```

**input-refs の更新ルール:**
- `03-decisions-overview.md` は `02-breakdown-overview.md` + `02-breakdown-validation.md` を参照する
- `components/03-decisions-{compId}.md` は `components/{compId}/02-breakdown-{compId}.md` の該当コンポーネント部分を参照する
- `components/04-artifact-{compId}.md` は `components/03-decisions-{compId}.md` を参照する
- L3ファイルは対応する L2 ファイルを参照する
- `04-artifact-overview.md` は全 L2 ファイルを参照する
- `05-verification-overview.md` は `04-artifact-overview.md` を参照する
- `components/{compId}/05-verification-{compId}.md` は対応する L2/L3 ファイルを参照する
- `implementation/01-validation.md` は `detailed-design/05-verification-overview.md` + `04-artifact-overview.md` + 全 L2/L3 ファイルを参照する

### リスクID・未解決事項の扱い

全ファイル共通で `RISK-{phase略称}-NNN` 形式を使用する:

| フェーズ略称 | フェーズ |
|-----------|---------|
| REQ | 要件定義 |
| BD | 基本設計 |
| DD | 詳細設計 |
| IMP | 実装 |
| TST | テスト |
| REL | リリース |

- セクション名は全フェーズ共通で「**未解決事項・リスク**」とする
- コンポーネント別ファイルのリスクIDはコンポーネント内で連番とする（例: `RISK-DD-{compId}-001` 〜）
- `03-decisions-overview.md` に全コンポーネントのリスク集約テーブルを設ける

---

## 各プロセスの責務定義

> **実装状況**: ✅ 設計完了 — 各プロセスの共通手順をオーケストレータおよびテンプレートに反映済み


| プロセス | 実行主体 | 入力 | 出力 | 検証軸 |
|---------|---------|------|------|--------|
| ①入力の検証 | AI | 前フェーズ⑤承認済みdoc（正本） | 差分`01-validation.md` → 正本マージ | 充足性・非矛盾性・明瞭性 |
| ②構成要素の分解 | AI | `01-validation.md`（正本） | 差分`02-breakdown.md` → 正本マージ | MECEな分解、依存関係の明示 |
| ③意思決定・検討 | AI提案→**人間承認** | `02-breakdown.md`（正本） | 差分`03-decisions.md` → 正本マージ | メリット/デメリット、選択根拠 |
| ④成果物の作成 | AI | `03-decisions.md` approved（正本） | 差分`04-artifact.md` → 正本マージ | フェーズ固有の品質基準 |
| ⑤成果物の検証 | AI検証→**人間承認** | `04-artifact.md`（正本） | 差分`05-verification.md` → 正本マージ | 要件トレーサビリティ、品質基準 |

**各プロセスの共通手順:**
1. 差分ドキュメントを `iter/iterN/phaseX/` に作成する
2. 差分ドキュメントのステータスが `approved` になったら正本へマージする
3. 正本の `version` をインクリメント・`updated-at` を更新する
4. ダッシュボードを更新する（フックが自動実行）
5. 正本へのマージ後、ドキュメント間で内容の不整合がないか検証する

---

## ダッシュボード

> **実装状況**: 🚧 一部実装 — ダッシュボードテンプレート（`.github/templates/dashboard.md`）作成済み。`PostToolUse` フックによる自動更新は**未実装**（⏸ フック作成フェーズで対応）

`docs/dashboard.md` はプロジェクト全体の進捗とボトルネックを可視化する。

### 更新ルール
- **作業着手前に必ず最新状態**に更新する
- `docs/**/*.md` および `iter/**/*.md` への書き込みを `PostToolUse` フックがトリガーし**自動更新**する
- セッションが中断・再開された場合も、オーケストレータはダッシュボードを起点に状態を復元する

### ダッシュボード構造（例）

```markdown
---
doc-type: dashboard
last-updated: "YYYY-MM-DD HH:MM"
---

# プロジェクトダッシュボード

## 現在のフェーズ / イテレーション
- フェーズ: 詳細設計
- イテレーション: 1

## フェーズ × プロセス ステータスマトリクス

| フェーズ     | ① | ② | ②v | ③ | ④ | ⑤ |
|------------|---|---|-----|---|---|---|
| 要件定義     | ✅ | ✅ | ─   | ✅ | ✅ | ✅ |
| 基本設計     | ✅ | ✅ | ─   | ✅ | ✅ | ✅ |
| 詳細設計     | ✅ | ✅ | ✅   | ⏳ | ─  | ─  |
| 実装         | ─  | ─  | ─   | ─  | ─  | ─  |
| テスト       | ─  | ─  | ─   | ─  | ─  | ─  |
| リリース     | ─  | ─  | ─   | ─  | ─  | ─  |

> ②v列 は詳細設計フェーズのみ有効（`02-breakdown-validation.md`）。他フェーズは ─ 固定。

凡例: ✅ approved / ⏳ awaiting-approval / 📝 draft / ❌ rejected / ─ not-started

## 詳細設計 コンポーネント別進捗（iter1）

| コンポーネントID | ③決定 | ④サマリ | ④API | ④Schema | ④Domain | ④TestCase | ⑤検証 |
|-------------|------|---------|------|---------|---------|-----------|------|
| COMP-001 | ✅ | 📝 | ─ | ─ | ─ | ─ | ─ |
| COMP-002 | ⏳ | ─ | ─ | ─ | ─ | ─ | ─ |

## ボトルネック
- `docs/detailed-design/03-decisions-overview.md`: awaiting-approval（未承認）

## 次アクション
- 詳細設計③の人間承認を取得 → フェーズゲート解除後に詳細設計④へ進行可能
```

### フック自動更新の仕組み

```
PostToolUse（対象: docs/**/*.md, iter/**/*.md への書き込み）:
  1. 更新されたファイルのフロントマターからステータスを読み取る
  2. dashboard.md のステータスマトリクスを更新する
  3. ボトルネック（awaiting-approval / rejected）を再計算する
  4. last-updated を現在時刻に更新する
```

---

## ダッシュボード確認/更新スキル

> **実装状況**: ⏸ スキル未作成

各フェーズのテンプレート構成要素に合わせたダッシュボード確認・更新手順を、フェーズごとの **`dashboard-sync-{phase}` スキル**として切り出す。オーケストレータはフェーズ遷移時にこのスキルを参照し、ダッシュボードのステータスマトリクスおよびコンポーネント別進捗を正確に更新する。

### スキル一覧

| スキル名 | 対象フェーズ | 主な確認/更新内容 |
|---------|-----------|----------------|
| `dashboard-sync-requirements` | 要件定義 | ①〜⑤のステータス + イテレーション別スコープファイルの存在確認 |
| `dashboard-sync-basic-design` | 基本設計 | ①〜⑤のステータス + コンポーネント仕様の完成度 |
| `dashboard-sync-detailed-design` | 詳細設計 | ①〜⑤ + ②vのステータス + コンポーネント別進捗テーブル更新 |
| `dashboard-sync-implementation` | 実装 | ①〜⑤のステータス + タスク消化率 + テストパス率 |
| `dashboard-sync-testing` | テスト | ①〜⑤のステータス + 品質ゲート充足状況 |
| `dashboard-sync-release` | リリース | ①〜⑤のステータス + デプロイ結果 + スモークテスト結果 |

### スキルの共通手順
1. 対象フェーズの全ドキュメントのフロントマターを走査する
2. `status` フィールドから各プロセスのステータスを取得する
3. ダッシュボードの該当行を更新する
4. フェーズ固有の詳細トラッキングセクションを更新する（例: 詳細設計のコンポーネント別進捗）
5. ボトルネック・次アクションを再計算する
6. `last-updated` を現在時刻に更新する

---

## NG時の差し戻しルーティング

> **実装状況**: ⏸ スキル未作成

①入力検証（`01-validation.md`）と⑤成果物検証（`05-verification.md`）でNG（FAIL / CONDITIONAL PASS）となった場合、**`routing-on-failure` スキル**（全フェーズ共通の1スキル）に基づいて適切なプロセスへ差し戻す。オーケストレータはこのスキルを参照して差し戻し先を判定する。

### 差し戻し判断基準

#### ①入力検証NG時
| NG理由 | 差し戻し先 | 説明 |
|-------|----------|------|
| 前フェーズの成果物が不完全・未承認 | 前フェーズの④または⑤ | 前フェーズの成果物を補完・再承認 |
| 前フェーズの成果物間に矛盾 | 前フェーズの③ | 意思決定の再検討 |
| 要件自体の不備（前フェーズのスコープ外） | 要件定義フェーズの② | 要件の再分解・再定義 |

#### ⑤成果物検証NG時
| NG理由 | 差し戻し先 | 説明 |
|-------|----------|------|
| 成果物の品質基準未達（軽微） | 同フェーズの④ | 成果物の修正・補完 |
| 意思決定内容と成果物の不一致 | 同フェーズの③ | 意思決定の再検討 |
| 分解の粒度・範囲が不適切 | 同フェーズの② | 分解からやり直し |
| 上流の前提条件に誤り | 前フェーズの該当プロセス | 上流への差し戻し |

### 差し戻しフロー
1. NG判定のドキュメントに `status: rejected` を設定する
2. `routing-on-failure` スキルの判断基準に基づき差し戻し先を特定する
3. 差し戻し先のドキュメントの `status` を `draft` に戻す
4. ダッシュボードを更新する（`dashboard-sync-{phase}` スキル経由）
5. 差し戻し理由を `05-verification.md` または `01-validation.md` の指摘事項セクションに記録する

---

## ダッシュボード整合性チェックとオーケストレーション

> **実装状況**: 🚧 一部実装 — オーケストレータ（`.github/agents/orchestrator.agent.md`）に整合性チェック手順・委譲ルールを実装済み。整合性チェックスキルは**未作成**（⏸ スキル作成フェーズで対応）。`dashboard-sync-{phase}` スキル・`routing-on-failure` スキル・フェーズ別サブエージェントも**未作成**（⏸）


オーケストレータ（メインエージェント）はサブエージェントへの委譲前に以下を実行する。

### 整合性チェック手順
1. `docs/dashboard.md` を読み込む
2. `docs/<phase>/` および `iter/iterN/phaseX/` のMarkdownファイルのフロントマターを走査する
3. ダッシュボードのステータスとファイルの実態を比較する
4. 不整合が検出された場合: **ディレクトリの実態を正**としてダッシュボードを更新する
5. 整合確認後、適切なフェーズ・プロセスのサブエージェントへ委譲する

### 委譲ルール

```
オーケストレータ:
  1. ダッシュボード読み込み → dashboard-sync-{phase} スキルで整合性チェック → 必要なら修正
  2. 現在フェーズ・プロセスを特定する
  3. 次に進むべきアクションを判定:
     a. approval-required doc が awaiting-approval
        → 人間承認を促す（フックがブロック）
     b. 01-validation または 05-verification が rejected
        → routing-on-failure スキルで差し戻し先を判定 → 対応サブエージェントへ委譲
     c. 詳細設計の 02-breakdown-validation が FAIL
        → 02-breakdown-overview / 02-breakdown-components へ差し戻し
     d. 次プロセスの差分docが未作成
        → 対応フェーズのサブエージェントへ委譲
     e. 差分docが作成済み・未マージ
        → マージ処理サブエージェントへ委譲
  4. サブエージェントの完了後、dashboard-sync-{phase} スキルでダッシュボードを再検証する
```

---

## 決定済み方針まとめ

> **実装状況**: 以下の表を参照


| 項目 | 採用方針 |
|------|---------|
| フェーズゲート強制 | `PreToolUse` フックで機械的にブロック |
| 実装フェーズ④ | `src/` にコード配置・`04-artifact.md` はサマリ＋参照リスト |
| TDD | 詳細設計でテストケース先行設計、実装で Red→Green→Refactor |
| 大規模要求 | フェーズ2以降を複数イテレーションに分割 |
| ドキュメント管理 | 正本（`docs/`）＋差分（`iter/`）の2種類、承認後に正本へマージ |
| ダッシュボード | `docs/dashboard.md`・`PostToolUse` フックで自動更新・作業着手前に確認 |
| 整合性チェック | オーケストレータが委譲前に確認、不整合はディレクトリを正として修正 |
| ダイアグラム | Mermaid または PlantUML で記述。テキストアート表現禁止 |
| 承認タイムスタンプ | `approved-at` フィールドで承認日時を自動記録（`03-decisions.md`, `05-verification.md`） |
| 要件PRD分割 | イテレーション別に `04-artifact-iterN.md` へファイル分割。本体は概要＋リンクのみ |
| 詳細設計分割 | 3層構造（全体サマリ → コンポーネントサマリ → 設計項目）でファイル分割 |
| 詳細設計②検証 | `02-breakdown-validation.md` でサブプロセスとして分解の妥当性を検証 |
| リスクID | `RISK-{phase略称}-NNN` 形式で統一。セクション名「未解決事項・リスク」 |
| ダッシュボードスキル | `dashboard-sync-{phase}` スキルでフェーズ別に確認/更新手順を定義 |
| NG差し戻し | `routing-on-failure` スキルで①⑤NG時の差し戻し先を判定 |
