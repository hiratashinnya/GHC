# testcase: check_phase_gate.py

対象スクリプト: `.github/hooks/scripts/entrypoints/check_phase_gate.py`

---

## テストケース一覧

| テストID | 観点 | 入力 | 期待動作 |
|----------|------|------|----------|
| CG-001 | `_scalar` 通常文字列 | `"hello"` | `"hello"` を返す |
| CG-002 | `_scalar` bool 真 | `"true"` | `True` を返す |
| CG-003 | `_scalar` bool 偽 | `"false"` | `False` を返す |
| CG-004 | `_scalar` null | `"null"` | `None` を返す |
| CG-005 | `_scalar` 整数 | `"5"` | `5` を返す |
| CG-006 | `_scalar` クォート付き文字列 | `'"foo"'` | `"foo"` を返す（クォート除去） |
| CG-007 | `_scalar` 空文字列 | `""` | `None` を返す |
| CG-008 | `parse_frontmatter` 正常なフロントマター有り | `approval-required: true` などを含む `.md` ファイル | フィールドを含む dict を返す |
| CG-009 | `parse_frontmatter` フロントマターなし | 通常のテキストのみの `.md` ファイル | `None` を返す |
| CG-010 | `parse_frontmatter` 存在しないパス | 読み取り不能なパス | `None` を返す |
| CG-011 | `infer_process` `01-` プレフィックス | `"01-validation.md"` | `1` を返す |
| CG-012 | `infer_process` `05-` プレフィックス（複合名） | `"05-verification-comp.md"` | `5` を返す |
| CG-013 | `infer_process` 不一致ファイル名 | `"README.md"` | `None` を返す |
| CG-014 | `parse_target` docs パス（相対 POSIX） | `"docs/basic-design/01-validation.md"` | `scope:"docs"`, `phase:"basic-design"`, `process:1` を返す |
| CG-015 | `parse_target` iter パス | `"iter/iter2/phase3/04-artifact.md"` | `scope:"iter"`, `phase:"detailed-design"`, `process:4`, `iteration:2` を返す |
| CG-016 | `parse_target` Windows バックスラッシュ | `"docs\\basic-design\\01-validation.md"` | CG-014 と同一の結果を返す |
| CG-017 | `parse_target` 不正パス（docs 外） | `"src/foo.py"` | `None` を返す |
| CG-018 | `required_gate_specs` process=1 かつ phase_index>1 | `process=1, phase_index=2` | 前フェーズ process=5 の spec が含まれる |
| CG-019 | `required_gate_specs` process>=4 | `process=4, phase="basic-design"` | 同フェーズ process=3 の spec が含まれる |
| CG-020 | `required_gate_specs` 要件なし | `process=2, phase_index=1` | specs が空リスト `[]` になる |
| CG-021 | `evaluate` ゲートドキュメント不在（missing） | gate_docs が空リスト | `blocked=True`, `missing_requirements` に要件情報が含まれる |
| CG-022 | `evaluate` ゲートドキュメント未承認（violation） | `status="draft"` のゲートドキュメント有り | `blocked=True`, `violations` に該当ドキュメントが含まれる |
| CG-023 | `evaluate` ゲートドキュメント承認済み | `status="approved"` のゲートドキュメント有り | `blocked=False`, `violations` と `missing_requirements` が空 |
| CG-024 | `collect_gate_docs` dashboard.md 除外 | `dashboard.md` を含むフォルダを走査 | 結果リストに dashboard.md が含まれない |
| CG-025 | `collect_gate_docs` approval-required フィルタ | `approval-required: true` / `false` 混在フォルダ | `true` のドキュメントのみ収集される |
| CG-026 | `collect_gate_docs` 空ディレクトリ | docs/iter ディレクトリが空の状態 | 空リスト `[]` を返す |
