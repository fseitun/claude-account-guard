import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.resolve_allowed_emails import (
    longest_prefix_folder_key,
    normalize_allowed_emails,
    resolve_allowed_emails,
)


class TestNormalizeAllowedEmails(unittest.TestCase):
    def test_trims_and_drops_blanks(self):
        self.assertEqual(
            normalize_allowed_emails([" a@b.com ", "", "  ", "x@y.com"]),
            ["a@b.com", "x@y.com"],
        )

    def test_none_returns_empty(self):
        self.assertEqual(normalize_allowed_emails(None), [])

    def test_empty_list_returns_empty(self):
        self.assertEqual(normalize_allowed_emails([]), [])


class TestLongestPrefixFolderKey(unittest.TestCase):
    def test_picks_longest_prefix(self):
        keys = ["/a", "/a/b", "/a/b/c"]
        self.assertEqual(longest_prefix_folder_key("/a/b/c/d", keys), "/a/b/c")

    def test_exact_match(self):
        self.assertEqual(longest_prefix_folder_key("/a/b", ["/a/b"]), "/a/b")

    def test_no_match_returns_none(self):
        self.assertIsNone(longest_prefix_folder_key("/other", ["/a/b"]))

    def test_empty_keys_returns_none(self):
        self.assertIsNone(longest_prefix_folder_key("/a/b", []))

    def test_tilde_expansion(self):
        home = os.path.expanduser("~")
        result = longest_prefix_folder_key(f"{home}/work/proj", ["~/work"])
        self.assertEqual(result, "~/work")


class TestResolveAllowedEmails(unittest.TestCase):
    def test_non_empty_merged_wins_over_expected_by_folder(self):
        r = resolve_allowed_emails(
            ["a@b.com"],
            {"/home/work": {"allowedEmails": ["other@x.com"]}},
            "/home/work/proj",
        )
        self.assertEqual(r.allowed_emails, ["a@b.com"])
        self.assertEqual(r.source_hint, "settings")

    def test_empty_merged_uses_longest_prefix(self):
        folder_map = {
            "/home": {"allowedEmails": ["wrong@x.com"]},
            "/home/work": {"allowedEmails": ["work@corp.com"]},
        }
        r = resolve_allowed_emails([], folder_map, "/home/work/myproject")
        self.assertEqual(r.allowed_emails, ["work@corp.com"])
        self.assertEqual(r.source_hint, "expectedByFolder")
        self.assertEqual(r.matched_folder_key, "/home/work")

    def test_no_match_yields_empty(self):
        r = resolve_allowed_emails(
            [],
            {"/other": {"allowedEmails": ["a@b.com"]}},
            "/home/me",
        )
        self.assertEqual(r.allowed_emails, [])
        self.assertEqual(r.source_hint, "none")

    def test_none_workspace_yields_empty(self):
        r = resolve_allowed_emails([], {"/home": {"allowedEmails": ["a@b.com"]}}, None)
        self.assertEqual(r.source_hint, "none")

    def test_none_folder_map_yields_empty(self):
        r = resolve_allowed_emails([], None, "/home/work")
        self.assertEqual(r.source_hint, "none")

    def test_tilde_keys_work(self):
        home = os.path.expanduser("~")
        r = resolve_allowed_emails(
            [],
            {"~/work": {"allowedEmails": ["me@corp.com"]}},
            f"{home}/work/project",
        )
        self.assertEqual(r.allowed_emails, ["me@corp.com"])
        self.assertEqual(r.source_hint, "expectedByFolder")


if __name__ == "__main__":
    unittest.main()
