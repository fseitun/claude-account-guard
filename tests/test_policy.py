import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.policy import evaluate_account_policy


class TestEvaluateAccountPolicy(unittest.TestCase):
    def test_empty_allow_list_does_not_warn_when_email_present(self):
        r = evaluate_account_policy("a@b.com", [])
        self.assertEqual(r.level, "ok")

    def test_allow_list_requires_match(self):
        r = evaluate_account_policy("a@b.com", ["x@y.com"])
        self.assertEqual(r.level, "error")

    def test_allow_list_case_insensitive(self):
        r = evaluate_account_policy("A@B.com", ["a@b.com"])
        self.assertEqual(r.level, "ok")

    def test_no_email_is_warning(self):
        r = evaluate_account_policy(None, [])
        self.assertEqual(r.level, "warning")

    def test_empty_string_email_is_warning(self):
        r = evaluate_account_policy("", [])
        self.assertEqual(r.level, "warning")

    def test_whitespace_only_email_is_warning(self):
        r = evaluate_account_policy("   ", [])
        self.assertEqual(r.level, "warning")

    def test_email_in_allow_list_is_ok(self):
        r = evaluate_account_policy("me@corp.com", ["me@corp.com"])
        self.assertEqual(r.level, "ok")

    def test_error_has_reason(self):
        r = evaluate_account_policy("wrong@x.com", ["right@x.com"])
        self.assertEqual(r.level, "error")
        self.assertIn("wrong@x.com", r.reason)


if __name__ == "__main__":
    unittest.main()
