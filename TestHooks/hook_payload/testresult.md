# testresult: hook_payload.py

対象スクリプト: `.github/hooks/scripts/hook_payload.py`
実行日: 2026-05-11
コミットID: a41de1e
実行コマンド: `python -m unittest test_hook_payload -v`
総合結果: **PASS** (53/53)

---

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
| HP-024 | `deny` stdout JSON 内容 | `reason="理由"` | stdout に `permissionDecision:"deny"` + `permissionDecisionReason:"理由"` の JSON が出力される | 期待 JSON 一致 | PASS |
| HP-025 | `deny` 戻り値 | `reason="理由"` | `EXIT_BLOCK (2)` を返す | `2` | PASS |
| HP-026 | `block` stdout 無出力 | `stderr_message=""` | stdout に何も出力しない | stdout 空 | PASS |
| HP-027 | `block` 戻り値 | `stderr_message="msg"` | `EXIT_BLOCK (2)` を返す | `2` | PASS |
| HP-028 | `block` stderr 出力 | `stderr_message="msg"` | stderr に `"msg"` が出力される | `"msg"` | PASS |
| HP-029 | `warn` stdout JSON 内容 | `message="警告"` | stdout に `systemMessage:"警告"` の JSON が出力される | 期待 JSON 一致 | PASS |
| HP-030 | `warn` 戻り値 | `message="警告"` | `EXIT_OK (0)` を返す | `0` | PASS |
| HP-031 | `stop_session` stdout JSON 内容 | `reason="停止理由"` | stdout に `continue:false` + `stopReason:"停止理由"` の JSON が出力される | 期待 JSON 一致 | PASS |
| HP-032 | `stop_session` 戻り値 | `reason="停止理由"` | `EXIT_OK (0)` を返す | `0` | PASS |
| HP-033 | `ask` stdout JSON 内容 | `reason="確認してください"` | stdout に `permissionDecision:"ask"` の JSON が出力される | 期待 JSON 一致 | PASS |
| HP-034 | `ask` 戻り値 | `reason="確認してください"` | `EXIT_OK (0)` を返す | `0` | PASS |
| HP-035 | `block_post` stdout JSON 内容（context 無し） | `reason="r"` | stdout に `decision:"block"` + `reason:"r"` の JSON が出力される | 期待 JSON 一致 | PASS |
| HP-036 | `block_post` stdout JSON 内容（context 有り） | `reason="r"`, `context="c"` | stdout に `additionalContext:"c"` が含まれる JSON が出力される | 期待 JSON 一致 | PASS |
| HP-037 | `block_post` 戻り値 | `reason="r"` | `EXIT_OK (0)` を返す | `0` | PASS |
| HP-038 | `add_context` stdout JSON 内容 | `text="追加情報"` | stdout に `additionalContext:"追加情報"` の JSON が出力される | 期待 JSON 一致 | PASS |
| HP-039 | `add_context` 戻り値 | `text="追加情報"` | `EXIT_OK (0)` を返す | `0` | PASS |
| HP-040 | `update_input` stdout JSON（context 無し） | `new_input={"filePath": "docs/new.md"}` | stdout に `updatedInput` が含まれ、`additionalContext` は含まれない | 期待 JSON 一致 | PASS |
| HP-041 | `update_input` stdout JSON（context 有り） | `new_input={}`, `context="ctx"` | stdout に `additionalContext:"ctx"` が含まれる | 期待 JSON 一致 | PASS |
| HP-042 | `update_input` 戻り値 | `new_input={}` | `EXIT_OK (0)` を返す | `0` | PASS |
| HP-043 | `block_stop` stdout JSON 内容 | `reason="停止ブロック"` | stdout に `hookSpecificOutput.decision:"block"` + `hookSpecificOutput.reason` の JSON が出力される | 期待 JSON 一致 | PASS |
| HP-044 | `block_stop` 戻り値 | `reason="停止ブロック"` | `EXIT_OK (0)` を返す | `0` | PASS |
| HP-045 | `block_subagent` stdout JSON 内容 | `reason="r"` | stdout にトップレベル `decision:"block"` + `reason:"r"` が出力され `hookSpecificOutput` は含まれない | 期待 JSON 一致 | PASS |
| HP-046 | `block_subagent` 戻り値 | `reason="r"` | `EXIT_OK (0)` を返す | `0` | PASS |
| HP-047 | `add_context` on PostToolUse | `text="t"` | stdout に `hookSpecificOutput.hookEventName:"PostToolUse"` + `additionalContext:"t"` が出力される | 期待 JSON 一致 | PASS |
| HP-048 | `add_context` on SessionStart | `text="t"` | stdout に `hookSpecificOutput.hookEventName:"SessionStart"` + `additionalContext:"t"` が出力される | 期待 JSON 一致 | PASS |
| HP-049 | `add_context` on SubagentStart | `text="t"` | stdout に `hookSpecificOutput.hookEventName:"SubagentStart"` + `additionalContext:"t"` が出力される | 期待 JSON 一致 | PASS |
| HP-050 | `read_payload` cp932 エンコーディング | cp932 でエンコードされた JSON バイト列（日本語含む） | dict を正常に返す（文字化けなし） | `{"hookEventName": "PreToolUse", "prompt": "テスト"}` | PASS |
| HP-051 | `read_payload` OSError 時の stderr 出力 | `stdin.buffer.read` が `OSError` を送出 | `{}` を返し、stderr に `"stdin read error"` を含むメッセージが出力される | 期待通り | PASS |
| HP-052 | `read_payload` 無効 JSON 時の stderr 出力 | バイト列 `"not valid json"` | `{}` を返し、stderr に `"JSON parse error"` を含むメッセージが出力される | 期待通り | PASS |
| HP-053 | `read_payload` デコード不可バイト列 | UTF-8 / cp932 どちらでもデコード不可なバイト列 | `{}` を返す（クラッシュしない） | `{}` | PASS |
