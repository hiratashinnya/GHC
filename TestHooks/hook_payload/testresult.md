# testresult: hook_payload.py

対象スクリプト: `.github/hooks/scripts/core/hook_payload.py`
実行日: 2026-05-21
コミットID: e4b618f
実行コマンド: `cd TestHooks/hook_payload && python -m unittest test_hook_payload -v`
総合結果: **FAIL** (32/55, errors=23)

---

## 備考付きサマリ（失敗行の注記）

- 失敗対象: 出力系メソッドのテスト（HP-024/025, HP-029-049 の一部）
- 共通エラー: `AttributeError: '_io.StringIO' object has no attribute 'buffer'`
- 発生箇所: `core/hook_output.py` の `emit_output()` が `sys.stdout.buffer.write(...)` を前提としているため、`StringIO` を使うテストで失敗

## 失敗詳細（期待値/実際値/原因/次アクション）

- 期待値: 各メソッド（`warn`/`deny`/`ask`/`stop_session`/`update_input`/`add_context` など）が stdout に JSON を出力し、`EXIT_OK` を返す。
- 実際値: `emit_output()` 呼び出し時に `AttributeError` が送出され、23テストが ERROR になった。
- 原因: テスト環境の `sys.stdout` が `StringIO` のため `.buffer` 属性を持たない。
- 対処理由（意思決定）: 今回PRでは実装改修を行わず、再現した失敗を testresult に正確に記録する方針を採用した。
- 判断根拠: 本PRのスコープは entrypoint 再配置であり、`emit_output()`/stdout モック互換の改修は別件として扱うべきため。
- 却下した案: ① `emit_output()` を即時修正して TextIO/BinaryIO 互換化する案 ② テスト側モックに `.buffer` を追加する案（いずれも本PRスコープ外として見送り）。
- 次アクション: `emit_output()` を `TextIO`/`BinaryIO` 両対応にするか、テスト側 stdout モックを `.buffer` 対応に変更して整合を取る。

## テスト結果

| テストID | 観点 | 入力 | 期待動作 | 結果 | 判定 |
|----------|------|------|----------|------|------|
| HP-001 | `PreToolUsePayload.from_dict` 全フィールド正常 | 全キー揃った PreToolUse ペイロード dict | 各フィールドが正しくマップされる | 全フィールド一致 | PASS |
| HP-002 | `PreToolUsePayload.from_dict` 欠落フィールド | 空 dict | 全フィールドがデフォルト値で生成される | `tool_name=""`, `tool_input={}`, `cwd=""` | PASS |
| HP-003 | `PostToolUsePayload.from_dict` tool_response 有り | `tool_response` キー付きペイロード | `tool_response` が保持される | `"file contents here"` | PASS |
| HP-004 | `PostToolUsePayload.from_dict` tool_response 無し | `tool_response` キーなし | `tool_response` が `None` になる | `None` | PASS |
| HP-005 | `UserPromptSubmitPayload.from_dict` prompt 取得 | `{"prompt": "hello", "hookEventName": "UserPromptSubmit"}` | `prompt == "hello"` | `"hello"` | PASS |
| HP-006 | `SessionStartPayload.from_dict` source 取得 | `{"source": "user"}` | `source == "user"` | `"user"` | PASS |
| HP-007 | `StopPayload.from_dict` stop_hook_active bool 変換 | `{"stop_hook_active": true}` | `stop_hook_active is True` | `True` | PASS |
| HP-008 | `parse_payload` PreToolUse ディスパッチ | `hookEventName="PreToolUse"` | `PreToolUsePayload` インスタンスが返る | `PreToolUsePayload` | PASS |
| HP-009 | `parse_payload` PostToolUse ディスパッチ | `hookEventName="PostToolUse"` | `PostToolUsePayload` インスタンスが返る | `PostToolUsePayload` | PASS |
| HP-010 | `parse_payload` UserPromptSubmit ディスパッチ | `hookEventName="UserPromptSubmit"` | `UserPromptSubmitPayload` インスタンスが返る | `UserPromptSubmitPayload` | PASS |
| HP-011 | `parse_payload` Stop ディスパッチ | `hookEventName="Stop"` | `StopPayload` インスタンスが返る | `StopPayload` | PASS |
| HP-012 | `parse_payload` 未知イベント名 | `hookEventName="UnknownEvent"` | `CommonPayload` インスタンスが返る | `CommonPayload` | PASS |
| HP-013 | `read_payload` 有効 JSON（stdin mock） | UTF-8 バイト列 `{"hookEventName":"PostToolUse"}` | dict を返す | `{"hookEventName": "PostToolUse"}` | PASS |
| HP-014 | `read_payload` 無効 JSON（stdin mock） | バイト列 `"not json"` | `{}` を返す | `{}` | PASS |
| HP-015 | `parse_payload` SessionStart ディスパッチ | `hookEventName="SessionStart"` | `SessionStartPayload` インスタンスが返る | `SessionStartPayload` | PASS |
| HP-016 | `parse_payload` SubagentStart ディスパッチ | `hookEventName="SubagentStart"` | `SubagentStartPayload` インスタンスが返る | `SubagentStartPayload` | PASS |
| HP-017 | `parse_payload` SubagentStop ディスパッチ | `hookEventName="SubagentStop"` | `SubagentStopPayload` インスタンスが返る | `SubagentStopPayload` | PASS |
| HP-018 | `parse_payload` PreCompact ディスパッチ | `hookEventName="PreCompact"` | `PreCompactPayload` インスタンスが返る | `PreCompactPayload` | PASS |
| HP-019 | `SubagentStartPayload.from_dict` agent フィールド | `{"agent_id": "ag-1", "agent_type": "coding"}` | `agent_id=="ag-1"`, `agent_type=="coding"` | 両フィールド一致 | PASS |
| HP-020 | `SubagentStopPayload.from_dict` stop_hook_active | `{"stop_hook_active": true}` | `stop_hook_active is True` | `True` | PASS |
| HP-021 | `PreCompactPayload.from_dict` trigger フィールド | `{"trigger": "manual"}` | `trigger == "manual"` | `"manual"` | PASS |
| HP-022 | `read_payload` isatty=True（TTY） | `stdin.isatty()` が `True` を返す | `{}` を返す | `{}` | PASS |
| HP-023 | `read_payload` 空 stdin | stdin から空バイト列が読まれる | `{}` を返す | `{}` | PASS |
| HP-024 | `deny` stdout JSON 内容 | `reason="理由"` | stdout に `permissionDecision:"deny"` + `permissionDecisionReason:"理由"` の JSON が出力される | `AttributeError: '_io.StringIO' object has no attribute 'buffer'` | ERROR |
| HP-025 | `deny` 戻り値 | `reason="理由"` | `EXIT_OK (0)` を返す | `AttributeError: '_io.StringIO' object has no attribute 'buffer'` | ERROR |
| HP-026 | `block` stdout 無出力 | `stderr_message=""` | stdout に何も出力しない | stdout 空 | PASS |
| HP-027 | `block` 戻り値 | `stderr_message="msg"` | `EXIT_BLOCK (2)` を返す | `2` | PASS |
| HP-028 | `block` stderr 出力 | `stderr_message="msg"` | stderr に `"msg"` が出力される | `"msg"` | PASS |
| HP-029 | `warn` stdout JSON 内容 | `message="警告"` | stdout に `systemMessage:"警告"` の JSON が出力される | `AttributeError: '_io.StringIO' object has no attribute 'buffer'` | ERROR |
| HP-030 | `warn` 戻り値 | `message="警告"` | `EXIT_OK (0)` を返す | `AttributeError: '_io.StringIO' object has no attribute 'buffer'` | ERROR |
| HP-031 | `stop_session` stdout JSON 内容 | `reason="停止理由"` | stdout に `continue:false` + `stopReason:"停止理由"` の JSON が出力される | `AttributeError: '_io.StringIO' object has no attribute 'buffer'` | ERROR |
| HP-032 | `stop_session` 戻り値 | `reason="停止理由"` | `EXIT_OK (0)` を返す | `AttributeError: '_io.StringIO' object has no attribute 'buffer'` | ERROR |
| HP-033 | `ask` stdout JSON 内容 | `reason="確認してください"` | stdout に `permissionDecision:"ask"` の JSON が出力される | `AttributeError: '_io.StringIO' object has no attribute 'buffer'` | ERROR |
| HP-034 | `ask` 戻り値 | `reason="確認してください"` | `EXIT_OK (0)` を返す | `AttributeError: '_io.StringIO' object has no attribute 'buffer'` | ERROR |
| HP-035 | `block_post` stdout JSON 内容（context 無し） | `reason="r"` | stdout に `decision:"block"` + `reason:"r"` の JSON が出力される | `AttributeError: '_io.StringIO' object has no attribute 'buffer'` | ERROR |
| HP-036 | `block_post` stdout JSON 内容（context 有り） | `reason="r"`, `context="c"` | stdout に `additionalContext:"c"` が含まれる JSON が出力される | `AttributeError: '_io.StringIO' object has no attribute 'buffer'` | ERROR |
| HP-037 | `block_post` 戻り値 | `reason="r"` | `EXIT_OK (0)` を返す | `AttributeError: '_io.StringIO' object has no attribute 'buffer'` | ERROR |
| HP-038 | `add_context` stdout JSON 内容 | `text="追加情報"` | stdout に `additionalContext:"追加情報"` の JSON が出力される | `AttributeError: '_io.StringIO' object has no attribute 'buffer'` | ERROR |
| HP-039 | `add_context` 戻り値 | `text="追加情報"` | `EXIT_OK (0)` を返す | `AttributeError: '_io.StringIO' object has no attribute 'buffer'` | ERROR |
| HP-040 | `update_input` stdout JSON（context 無し） | `new_input={"filePath": "docs/new.md"}` | stdout に `updatedInput` が含まれ、`additionalContext` は含まれない | `AttributeError: '_io.StringIO' object has no attribute 'buffer'` | ERROR |
| HP-041 | `update_input` stdout JSON（context 有り） | `new_input={}`, `context="ctx"` | stdout に `additionalContext:"ctx"` が含まれる | `AttributeError: '_io.StringIO' object has no attribute 'buffer'` | ERROR |
| HP-042 | `update_input` 戻り値 | `new_input={}` | `EXIT_OK (0)` を返す | `AttributeError: '_io.StringIO' object has no attribute 'buffer'` | ERROR |
| HP-043 | `block_stop` stdout JSON 内容 | `reason="停止ブロック"` | stdout に `hookSpecificOutput.decision:"block"` + `hookSpecificOutput.reason` の JSON が出力される | `AttributeError: '_io.StringIO' object has no attribute 'buffer'` | ERROR |
| HP-044 | `block_stop` 戻り値 | `reason="停止ブロック"` | `EXIT_OK (0)` を返す | `AttributeError: '_io.StringIO' object has no attribute 'buffer'` | ERROR |
| HP-045 | `block_subagent` stdout JSON 内容 | `reason="r"` | stdout にトップレベル `decision:"block"` + `reason:"r"` が出力され `hookSpecificOutput` は含まれない | `AttributeError: '_io.StringIO' object has no attribute 'buffer'` | ERROR |
| HP-046 | `block_subagent` 戻り値 | `reason="r"` | `EXIT_OK (0)` を返す | `AttributeError: '_io.StringIO' object has no attribute 'buffer'` | ERROR |
| HP-047 | `add_context` on PostToolUse | `text="t"` | stdout に `hookSpecificOutput.hookEventName:"PostToolUse"` + `additionalContext:"t"` が出力される | `AttributeError: '_io.StringIO' object has no attribute 'buffer'` | ERROR |
| HP-048 | `add_context` on SessionStart | `text="t"` | stdout に `hookSpecificOutput.hookEventName:"SessionStart"` + `additionalContext:"t"` が出力される | `AttributeError: '_io.StringIO' object has no attribute 'buffer'` | ERROR |
| HP-049 | `add_context` on SubagentStart | `text="t"` | stdout に `hookSpecificOutput.hookEventName:"SubagentStart"` + `additionalContext:"t"` が出力される | `AttributeError: '_io.StringIO' object has no attribute 'buffer'` | ERROR |
| HP-050 | `read_payload` cp932 エンコーディング | cp932 でエンコードされた JSON バイト列（日本語含む） | dict を正常に返す（文字化けなし） | `{"hookEventName": "PreToolUse", "prompt": "テスト"}` | PASS |
| HP-051 | `read_payload` OSError 時の stderr 出力 | `stdin.buffer.read` が `OSError` を送出 | `{}` を返し、stderr に `"stdin read error"` を含むメッセージが出力される | 期待通り | PASS |
| HP-052 | `read_payload` 無効 JSON 時の stderr 出力 | バイト列 `"not valid json"` | `{}` を返し、stderr に `"JSON parse error"` を含むメッセージが出力される | 期待通り | PASS |
| HP-053 | `read_payload` デコード不可バイト列 | UTF-8 / cp932 どちらでもデコード不可なバイト列 | `{}` を返す（クラッシュしない） | `{}` | PASS |
| HP-054 | `get_hook_input` 高レベル入口 | stdin に `PreToolUse` JSON が流れる | `read + parse + dispatch` が1回で実行され `PreToolUsePayload` が返る | `PreToolUsePayload` | PASS |
| HP-055 | facade 互換公開 | `hook_payload` import | `get_hook_input` が facade から import できる | callable であることを確認 | PASS |
