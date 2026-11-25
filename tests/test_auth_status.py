import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.auth_status import parse_auth_status


class TestParseAuthStatus(unittest.TestCase):
    def test_logged_in_with_email(self):
        s = parse_auth_status(0, json.dumps({"loggedIn": True, "email": " me@corp.com "}))
        self.assertEqual((s.state, s.email), ("known", "me@corp.com"))

    def test_logged_out_exits_nonzero_but_is_known(self):
        s = parse_auth_status(1, json.dumps({"loggedIn": False, "authMethod": "none"}))
        self.assertEqual((s.state, s.email), ("known", None))

    def test_logged_in_without_email_is_unknown(self):
        s = parse_auth_status(0, json.dumps({"loggedIn": True, "authMethod": "apiKey"}))
        self.assertEqual(s.state, "unknown")

    def test_non_json_is_unknown(self):
        s = parse_auth_status(127, "claude: command not found")
        self.assertEqual(s.state, "unknown")

    def test_empty_output_is_unknown(self):
        self.assertEqual(parse_auth_status(1, "").state, "unknown")

    def test_non_object_json_is_unknown(self):
        self.assertEqual(parse_auth_status(0, "[]").state, "unknown")


if __name__ == "__main__":
    unittest.main()
