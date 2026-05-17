#!/usr/bin/env python3
"""Unit tests for hook_payload.py"""

from __future__ import annotations

import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

SCRIPTS_DIR = Path(r"c:\GHC\.github\hooks\scripts")
sys.path.insert(0, str(SCRIPTS_DIR))

from hook_payload import (
    EXIT_OK,
    EXIT_BLOCK,
    get_hook_input,
    read_payload,
    parse_payload,
    CommonPayload,
    PreToolUsePayload,
    PostToolUsePayload,
    UserPromptSubmitPayload,
    SessionStartPayload,
    StopPayload,
    SubagentStartPayload,
    SubagentStopPayload,
    PreCompactPayload,
)


class TestPreToolUsePayload(unittest.TestCase):

    def test_HP001_from_dict_all_fields(self):
        d = {
            "hookEventName": "PreToolUse",
            "cwd": "/workspace",
            "sessionId": "sess-1",
            "timestamp": "2026-01-01",
            "tool_name": "create_file",
            "tool_input": {"filePath": "docs/x.md"},
            "tool_use_id": "tu-1",
        }
        p = PreToolUsePayload.from_dict(d)
        self.assertEqual(p.hook_event_name, "PreToolUse")
        self.assertEqual(p.cwd, "/workspace")
        self.assertEqual(p.session_id, "sess-1")
        self.assertEqual(p.tool_name, "create_file")
        self.assertEqual(p.tool_input, {"filePath": "docs/x.md"})
        self.assertEqual(p.tool_use_id, "tu-1")

    def test_HP002_from_dict_missing_fields(self):
        p = PreToolUsePayload.from_dict({})
        self.assertEqual(p.tool_name, "")
        self.assertEqual(p.tool_input, {})
        self.assertEqual(p.cwd, "")


class TestPostToolUsePayload(unittest.TestCase):

    def test_HP003_from_dict_tool_response_present(self):
        d = {
            "hookEventName": "PostToolUse",
            "tool_name": "read_file",
            "tool_input": {},
            "tool_response": "file contents here",
        }
        p = PostToolUsePayload.from_dict(d)
        self.assertEqual(p.tool_response, "file contents here")

    def test_HP004_from_dict_tool_response_absent(self):
        p = PostToolUsePayload.from_dict({"hookEventName": "PostToolUse"})
        self.assertIsNone(p.tool_response)


class TestUserPromptSubmitPayload(unittest.TestCase):

    def test_HP005_prompt_field(self):
        d = {"hookEventName": "UserPromptSubmit", "prompt": "hello"}
        p = UserPromptSubmitPayload.from_dict(d)
        self.assertEqual(p.prompt, "hello")


class TestSessionStartPayload(unittest.TestCase):

    def test_HP006_source_field(self):
        p = SessionStartPayload.from_dict({"source": "user"})
        self.assertEqual(p.source, "user")


class TestStopPayload(unittest.TestCase):

    def test_HP007_stop_hook_active_bool(self):
        p = StopPayload.from_dict({"stop_hook_active": True})
        self.assertIs(p.stop_hook_active, True)


class TestParsePayload(unittest.TestCase):

    def test_HP008_dispatch_pre_tool_use(self):
        result = parse_payload({"hookEventName": "PreToolUse"})
        self.assertIsInstance(result, PreToolUsePayload)

    def test_HP009_dispatch_post_tool_use(self):
        result = parse_payload({"hookEventName": "PostToolUse"})
        self.assertIsInstance(result, PostToolUsePayload)

    def test_HP010_dispatch_user_prompt_submit(self):
        result = parse_payload({"hookEventName": "UserPromptSubmit"})
        self.assertIsInstance(result, UserPromptSubmitPayload)

    def test_HP011_dispatch_stop(self):
        result = parse_payload({"hookEventName": "Stop"})
        self.assertIsInstance(result, StopPayload)

    def test_HP012_unknown_event_name(self):
        result = parse_payload({"hookEventName": "UnknownEvent"})
        self.assertIsInstance(result, CommonPayload)
        # Unknown イベントは CommonPayload のサブクラスであってはならない
        self.assertNotIsInstance(result, PreToolUsePayload)

    def test_HP015_dispatch_session_start(self):
        result = parse_payload({"hookEventName": "SessionStart"})
        self.assertIsInstance(result, SessionStartPayload)

    def test_HP016_dispatch_subagent_start(self):
        result = parse_payload({"hookEventName": "SubagentStart"})
        self.assertIsInstance(result, SubagentStartPayload)

    def test_HP017_dispatch_subagent_stop(self):
        result = parse_payload({"hookEventName": "SubagentStop"})
        self.assertIsInstance(result, SubagentStopPayload)

    def test_HP018_dispatch_pre_compact(self):
        result = parse_payload({"hookEventName": "PreCompact"})
        self.assertIsInstance(result, PreCompactPayload)


class TestSubagentStartPayload(unittest.TestCase):

    def test_HP019_from_dict_agent_fields(self):
        d = {"agent_id": "ag-1", "agent_type": "coding"}
        p = SubagentStartPayload.from_dict(d)
        self.assertEqual(p.agent_id, "ag-1")
        self.assertEqual(p.agent_type, "coding")


class TestSubagentStopPayload(unittest.TestCase):

    def test_HP020_from_dict_stop_hook_active(self):
        p = SubagentStopPayload.from_dict({"stop_hook_active": True})
        self.assertIs(p.stop_hook_active, True)


class TestPreCompactPayload(unittest.TestCase):

    def test_HP021_from_dict_trigger_field(self):
        p = PreCompactPayload.from_dict({"trigger": "manual"})
        self.assertEqual(p.trigger, "manual")


class TestReadPayload(unittest.TestCase):

    def _mock_stdin(self, data: bytes):
        mock = MagicMock()
        mock.isatty.return_value = False
        mock.buffer.read.return_value = data
        return mock

    def test_HP013_valid_json(self):
        with patch("hook_input.sys.stdin", self._mock_stdin(b'{"hookEventName":"PostToolUse"}')):
            result = read_payload()
        self.assertEqual(result, {"hookEventName": "PostToolUse"})

    def test_HP014_invalid_json(self):
        with patch("hook_input.sys.stdin", self._mock_stdin(b"not json")):
            result = read_payload()
        self.assertEqual(result, {})

    def test_HP022_isatty_returns_empty_dict(self):
        mock = MagicMock()
        mock.isatty.return_value = True
        with patch("hook_input.sys.stdin", mock):
            result = read_payload()
        self.assertEqual(result, {})

    def test_HP023_empty_stdin_returns_empty_dict(self):
        mock = MagicMock()
        mock.isatty.return_value = False
        mock.buffer.read.return_value = b""
        with patch("hook_input.sys.stdin", mock):
            result = read_payload()
        self.assertEqual(result, {})

    def test_HP050_cp932_encoded_payload(self):
        """cp932 エンコードのペイロードを正常にデコードできることを確認。"""
        payload = {"hookEventName": "PreToolUse", "prompt": "テスト"}
        raw_bytes = json.dumps(payload, ensure_ascii=False).encode("cp932")
        mock = MagicMock()
        mock.isatty.return_value = False
        mock.buffer.read.return_value = raw_bytes
        with patch("hook_input.sys.stdin", mock):
            result = read_payload()
        self.assertEqual(result["hookEventName"], "PreToolUse")
        self.assertEqual(result["prompt"], "テスト")

    def test_HP051_stdin_os_error_writes_stderr(self):
        """OSError 発生時に stderr にエラーメッセージを出力することを確認。"""
        mock = MagicMock()
        mock.isatty.return_value = False
        mock.buffer.read.side_effect = OSError("pipe broken")
        buf = io.StringIO()
        with patch("hook_input.sys.stdin", mock), patch("hook_input.sys.stderr", buf):
            result = read_payload()
        self.assertEqual(result, {})
        self.assertIn("stdin read error", buf.getvalue())

    def test_HP052_invalid_json_writes_stderr(self):
        """JSON パースエラー時に stderr にエラーメッセージを出力することを確認。"""
        mock = MagicMock()
        mock.isatty.return_value = False
        mock.buffer.read.return_value = b"not valid json"
        buf = io.StringIO()
        with patch("hook_input.sys.stdin", mock), patch("hook_input.sys.stderr", buf):
            result = read_payload()
        self.assertEqual(result, {})
        self.assertIn("JSON parse error", buf.getvalue())

    def test_HP053_undecodable_bytes_returns_empty(self):
        """UTF-8/cp932 どちらでもデコードできないバイト列は {} を返ず。"""
        # 0x80つ0x9fは cp932 の有効範囲の一部だが、UTF-8 の続バイトを持たないので
        # 両エンコードが失敗させるために e0 80 80 を使う
        raw_bytes = b"\xe0\x80\x80"  # over-long UTF-8; invalid in both utf-8 and cp932 as JSON
        mock = MagicMock()
        mock.isatty.return_value = False
        mock.buffer.read.return_value = raw_bytes
        buf = io.StringIO()
        with patch("hook_input.sys.stdin", mock), patch("hook_input.sys.stderr", buf):
            result = read_payload()
        # Over-long UTF-8 bytes decoded via cp932 would produce garbled JSON -> {} expected
        # OR if both fail -> replacement characters -> JSON error -> {}
        self.assertEqual(result, {})


class TestGetHookInput(unittest.TestCase):

    def test_HP054_get_hook_input_returns_typed_event(self):
        mock = MagicMock()
        mock.isatty.return_value = False
        mock.buffer.read.return_value = b'{"hookEventName":"PreToolUse","tool_name":"read_file"}'
        with patch("hook_input.sys.stdin", mock):
            result = get_hook_input()
        self.assertIsInstance(result, PreToolUsePayload)
        self.assertEqual(result.tool_name, "read_file")

    def test_HP055_get_hook_input_is_reexported_from_facade(self):
        self.assertTrue(callable(get_hook_input))


# ---------------------------------------------------------------------------
# Output method tests (moved from test_hook_output.py: HO-001 -> HP-024 etc.)
# ---------------------------------------------------------------------------

def _capture_stdout(fn, *args, **kwargs):
    """Call fn(*args, **kwargs) with stdout captured; return (return_value, stdout_text)."""
    buf = io.StringIO()
    with patch("sys.stdout", buf):
        ret = fn(*args, **kwargs)
    return ret, buf.getvalue()


class TestDeny(unittest.TestCase):

    def setUp(self):
        self.event = PreToolUsePayload(hook_event_name="PreToolUse")

    def test_HP024_deny_stdout_json(self):
        _, stdout = _capture_stdout(self.event.deny, "理由")
        data = json.loads(stdout.strip())
        hs = data["hookSpecificOutput"]
        self.assertEqual(hs["permissionDecision"], "deny")
        self.assertEqual(hs["permissionDecisionReason"], "理由")

    def test_HP025_deny_return_value(self):
        ret, _ = _capture_stdout(self.event.deny, "理由")
        self.assertEqual(ret, EXIT_OK)


class TestBlock(unittest.TestCase):

    def setUp(self):
        self.event = PreToolUsePayload(hook_event_name="PreToolUse")

    def test_HP026_block_no_stdout(self):
        _, stdout = _capture_stdout(self.event.block, "")
        self.assertEqual(stdout, "")

    def test_HP027_block_return_value(self):
        ret, _ = _capture_stdout(self.event.block, "msg")
        self.assertEqual(ret, EXIT_BLOCK)

    def test_HP028_block_stderr_message(self):
        buf = io.StringIO()
        with patch("sys.stderr", buf):
            self.event.block("msg")
        self.assertEqual(buf.getvalue().strip(), "msg")


class TestWarn(unittest.TestCase):

    def setUp(self):
        self.event = PostToolUsePayload(hook_event_name="PostToolUse")

    def test_HP029_warn_stdout_json(self):
        _, stdout = _capture_stdout(self.event.warn, "警告")
        data = json.loads(stdout.strip())
        self.assertEqual(data["systemMessage"], "警告")

    def test_HP030_warn_return_value(self):
        ret, _ = _capture_stdout(self.event.warn, "警告")
        self.assertEqual(ret, EXIT_OK)


class TestStopSession(unittest.TestCase):

    def setUp(self):
        self.event = StopPayload(hook_event_name="Stop")

    def test_HP031_stop_session_stdout_json(self):
        _, stdout = _capture_stdout(self.event.stop_session, "停止理由")
        data = json.loads(stdout.strip())
        self.assertFalse(data["continue"])
        self.assertEqual(data["stopReason"], "停止理由")

    def test_HP032_stop_session_return_value(self):
        ret, _ = _capture_stdout(self.event.stop_session, "停止理由")
        self.assertEqual(ret, EXIT_OK)


class TestAsk(unittest.TestCase):

    def setUp(self):
        self.event = PreToolUsePayload(hook_event_name="PreToolUse")

    def test_HP033_ask_stdout_json(self):
        _, stdout = _capture_stdout(self.event.ask, "確認してください")
        data = json.loads(stdout.strip())
        hs = data["hookSpecificOutput"]
        self.assertEqual(hs["permissionDecision"], "ask")
        self.assertEqual(hs["permissionDecisionReason"], "確認してください")

    def test_HP034_ask_return_value(self):
        ret, _ = _capture_stdout(self.event.ask, "確認してください")
        self.assertEqual(ret, EXIT_OK)


class TestBlockPost(unittest.TestCase):

    def setUp(self):
        self.event = PostToolUsePayload(hook_event_name="PostToolUse")

    def test_HP035_block_post_no_context(self):
        _, stdout = _capture_stdout(self.event.block_post, "r")
        data = json.loads(stdout.strip())
        self.assertEqual(data["decision"], "block")
        self.assertEqual(data["reason"], "r")

    def test_HP036_block_post_with_context(self):
        _, stdout = _capture_stdout(self.event.block_post, "r", "c")
        data = json.loads(stdout.strip())
        hs = data.get("hookSpecificOutput", {})
        self.assertEqual(hs.get("additionalContext"), "c")

    def test_HP037_block_post_return_value(self):
        ret, _ = _capture_stdout(self.event.block_post, "r")
        self.assertEqual(ret, EXIT_OK)


class TestAddContext(unittest.TestCase):

    def setUp(self):
        self.event = PostToolUsePayload(hook_event_name="PostToolUse")

    def test_HP038_add_context_stdout_json(self):
        _, stdout = _capture_stdout(self.event.add_context, "追加情報")
        data = json.loads(stdout.strip())
        hs = data["hookSpecificOutput"]
        self.assertEqual(hs["additionalContext"], "追加情報")

    def test_HP039_add_context_return_value(self):
        ret, _ = _capture_stdout(self.event.add_context, "追加情報")
        self.assertEqual(ret, EXIT_OK)


class TestUpdateInput(unittest.TestCase):

    def setUp(self):
        self.event = PreToolUsePayload(hook_event_name="PreToolUse")

    def test_HP040_update_input_stdout_json(self):
        new_input = {"filePath": "docs/new.md"}
        _, stdout = _capture_stdout(self.event.update_input, new_input)
        data = json.loads(stdout.strip())
        hs = data["hookSpecificOutput"]
        self.assertEqual(hs["updatedInput"], new_input)
        self.assertNotIn("additionalContext", hs)

    def test_HP041_update_input_with_context_stdout_json(self):
        new_input = {"filePath": "docs/new.md"}
        _, stdout = _capture_stdout(self.event.update_input, new_input, "ctx")
        data = json.loads(stdout.strip())
        hs = data["hookSpecificOutput"]
        self.assertEqual(hs["additionalContext"], "ctx")

    def test_HP042_update_input_return_value(self):
        ret, _ = _capture_stdout(self.event.update_input, {})
        self.assertEqual(ret, EXIT_OK)


class TestBlockStop(unittest.TestCase):

    def setUp(self):
        self.event = StopPayload(hook_event_name="Stop")

    def test_HP043_block_stop_stdout_json(self):
        _, stdout = _capture_stdout(self.event.block_stop, "停止ブロック")
        data = json.loads(stdout.strip())
        hs = data["hookSpecificOutput"]
        self.assertEqual(hs["decision"], "block")
        self.assertEqual(hs["reason"], "停止ブロック")

    def test_HP044_block_stop_return_value(self):
        ret, _ = _capture_stdout(self.event.block_stop, "停止ブロック")
        self.assertEqual(ret, EXIT_OK)


class TestBlockSubagent(unittest.TestCase):

    def setUp(self):
        self.event = SubagentStopPayload(hook_event_name="SubagentStop")

    def test_HP045_block_subagent_stdout_json(self):
        _, stdout = _capture_stdout(self.event.block_subagent, "r")
        data = json.loads(stdout.strip())
        self.assertEqual(data["decision"], "block")
        self.assertEqual(data["reason"], "r")
        self.assertNotIn("hookSpecificOutput", data)

    def test_HP046_block_subagent_return_value(self):
        ret, _ = _capture_stdout(self.event.block_subagent, "r")
        self.assertEqual(ret, EXIT_OK)


class TestAddContextPerEvent(unittest.TestCase):
    """add_context() is inherited via _ContextMixin — verify all 3 events."""

    def test_HP047_add_context_post_tool_use(self):
        event = PostToolUsePayload(hook_event_name="PostToolUse")
        _, stdout = _capture_stdout(event.add_context, "t")
        hs = json.loads(stdout.strip())["hookSpecificOutput"]
        self.assertEqual(hs["hookEventName"], "PostToolUse")
        self.assertEqual(hs["additionalContext"], "t")

    def test_HP048_add_context_session_start(self):
        event = SessionStartPayload(hook_event_name="SessionStart")
        _, stdout = _capture_stdout(event.add_context, "t")
        hs = json.loads(stdout.strip())["hookSpecificOutput"]
        self.assertEqual(hs["hookEventName"], "SessionStart")
        self.assertEqual(hs["additionalContext"], "t")

    def test_HP049_add_context_subagent_start(self):
        event = SubagentStartPayload(hook_event_name="SubagentStart")
        _, stdout = _capture_stdout(event.add_context, "t")
        hs = json.loads(stdout.strip())["hookSpecificOutput"]
        self.assertEqual(hs["hookEventName"], "SubagentStart")
        self.assertEqual(hs["additionalContext"], "t")


if __name__ == "__main__":
    unittest.main(verbosity=2)
