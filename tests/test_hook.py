import io
import json
import os
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "hooks"))

import account_guard_hook as hook

from lib.auth_status import AuthStatus

RULE = {"expectedByFolder": {"/work": {"allowedEmails": ["me@corp.com"]}}}


def run_hook(config, status, cwd="/work/repo", env=None):
    out, err, code = io.StringIO(), io.StringIO(), None
    stdin = io.StringIO(json.dumps({"cwd": cwd, "hook_event_name": "UserPromptSubmit"}))
    environ = {k: v for k, v in os.environ.items() if k != "CLAUDE_PLUGIN_OPTION_ON_MISMATCH"}
    environ.update(env or {})
    with (
        mock.patch.object(hook, "_read_account_guard_config", return_value=config),
        mock.patch.object(hook, "_read_auth_status", return_value=status),
        mock.patch.object(sys, "stdin", stdin),
        mock.patch.dict(os.environ, environ, clear=True),
        redirect_stdout(out),
        redirect_stderr(err),
    ):
        try:
            hook.main()
        except SystemExit as e:
            code = e.code
    return code, out.getvalue(), err.getvalue()


class TestHook(unittest.TestCase):
    def test_matching_account_is_silent(self):
        code, out, _ = run_hook(RULE, AuthStatus("known", "me@corp.com"))
        self.assertEqual((code, out), (0, ""))

    def test_no_rule_for_folder_is_silent(self):
        code, out, _ = run_hook(RULE, AuthStatus("known", "x@y.com"), cwd="/home")
        self.assertEqual((code, out), (0, ""))

    def test_mismatch_warn_reaches_user_and_claude(self):
        code, out, _ = run_hook(RULE, AuthStatus("known", "x@y.com"))
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertIn("x@y.com", data["systemMessage"])
        self.assertEqual(data["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        self.assertEqual(data["hookSpecificOutput"]["additionalContext"], data["systemMessage"])

    def test_mismatch_block_exits_2(self):
        config = {**RULE, "onMismatch": "block"}
        code, out, err = run_hook(config, AuthStatus("known", "x@y.com"))
        self.assertEqual((code, out), (2, ""))
        self.assertIn("x@y.com", err)

    def test_option_env_var_overrides_config_and_is_case_insensitive(self):
        env = {"CLAUDE_PLUGIN_OPTION_ON_MISMATCH": " Block "}
        code, _, _ = run_hook(RULE, AuthStatus("known", "x@y.com"), env=env)
        self.assertEqual(code, 2)

    def test_logged_out_blocks_in_block_mode(self):
        config = {**RULE, "onMismatch": "block"}
        code, _, err = run_hook(config, AuthStatus("known", None))
        self.assertEqual(code, 2)
        self.assertIn("Not logged in", err)

    def test_unknown_account_never_blocks(self):
        config = {**RULE, "onMismatch": "block"}
        status = AuthStatus("unknown", detail="`claude` is not on PATH for hooks.")
        code, out, err = run_hook(config, status)
        self.assertEqual((code, err), (0, ""))
        data = json.loads(out)
        self.assertIn("Could not check", data["systemMessage"])
        self.assertIn("not on PATH", data["hookSpecificOutput"]["additionalContext"])


if __name__ == "__main__":
    unittest.main()
