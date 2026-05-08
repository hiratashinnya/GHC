# testresult: check_phase_gate.py

対象スクリプト: `.github/hooks/scripts/check_phase_gate.py`
実行日: 2026-05-08
コミットID: d8db764 (未コミット変更あり: _lib 一元管理統合)
実行コマンド: `python -m unittest TestHooks/check_phase_gate/test_check_phase_gate.py -v`
総合結果: **PASS** (39/39)

---

## テスト結果

| テストID | クラス | 観点 | 結果 | 判定 |
|----------|--------|------|------|------|
| CG-001 | TestScalar | `_scalar` 通常文字列 | `"hello"` | PASS |
| CG-002 | TestScalar | `_scalar` bool 真 | `True` | PASS |
| CG-003 | TestScalar | `_scalar` bool 偽 | `False` | PASS |
| CG-004 | TestScalar | `_scalar` null | `None` | PASS |
| CG-005 | TestScalar | `_scalar` 整数 | `5` | PASS |
| CG-006 | TestScalar | `_scalar` クォート付き文字列 | `"foo"` | PASS |
| CG-007 | TestScalar | `_scalar` 空文字列 | `None` | PASS |
| CG-008 | TestParseFrontmatter | 正常なフロントマター | dict 返却 | PASS |
| CG-009 | TestParseFrontmatter | フロントマターなし | `None` | PASS |
| CG-010 | TestParseFrontmatter | 存在しないパス | `None` | PASS |
| CG-011 | TestInferProcess | `01-` プレフィックス | `1` | PASS |
| CG-012 | TestInferProcess | `05-` 複合名 | `5` | PASS |
| CG-013 | TestInferProcess | 不一致 | `None` | PASS |
| CG-014 | TestExtractVariant | variant なし | `None` | PASS |
| CG-015 | TestExtractVariant | overview variant | `"overview"` | PASS |
| CG-016 | TestExtractVariant | compId variant | `"auth"` | PASS |
| CG-017 | TestExtractVariant | artifact サブタイプ除去 | `"auth"` | PASS |
| CG-018 | TestExtractVariant | artifact サブタイプなし | `"auth"` | PASS |
| CG-019 | TestParseWriteTarget | docs 単純パス | scope/phase/process 一致 | PASS |
| CG-020 | TestParseWriteTarget | docs overview | variant="overview" | PASS |
| CG-021 | TestParseWriteTarget | docs components | variant="auth" | PASS |
| CG-022 | TestParseWriteTarget | iter パス | scope="iter", iteration=2 | PASS |
| CG-023 | TestParseWriteTarget | Windows バックスラッシュ | POSIX 版と一致 | PASS |
| CG-024 | TestParseWriteTarget | 不正パス | `None` | PASS |
| CG-025 | TestPrecedingGates | process=1, phase>1 | 前フェーズ proc=5 が含まれる | PASS |
| CG-026 | TestPrecedingGates | process=4, variant なし | 同フェーズ proc=3 のみ | PASS |
| CG-027 | TestPrecedingGates | process=4, compId variant | variant 版 + overview 版の両方 | PASS |
| CG-028 | TestPrecedingGates | ゲートなし条件 | 空リスト | PASS |
| CG-029 | TestExpectedPath | docs 単純 | 正規パス文字列 | PASS |
| CG-030 | TestExpectedPath | docs overview | `-overview` サフィックス | PASS |
| CG-031 | TestExpectedPath | docs compId | components/ サブディレクトリ | PASS |
| CG-032 | TestExpectedPath | iter | iter/iterN/phaseM/ パス | PASS |
| CG-033 | TestCheckGateCompliance | ゲート不要（requirements proc=2） | blocked=False | PASS |
| CG-034 | TestCheckGateCompliance | ゲートファイル不在 | blocked=True, missing=1 | PASS |
| CG-035 | TestCheckGateCompliance | ゲート承認済み | blocked=False | PASS |
| CG-036 | TestCheckGateCompliance | ゲート未承認（draft） | blocked=True, violations=1 | PASS |
| CG-037 | TestCheckGateCompliance | 命名規則違反（glob 検出） | blocked=True, naming_violations=1 | PASS |
| CG-038 | TestCheckGateCompliance | compId: variant+overview 両方承認 | blocked=False | PASS |
| CG-039 | TestCheckGateCompliance | compId: overview 不在 | blocked=True, missing に "overview" | PASS |
