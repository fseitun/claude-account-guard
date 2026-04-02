#!/usr/bin/env python3
"""UserPromptSubmit hook: enforce per-folder Claude account policy."""

import json
import os
import subprocess
import sys

PLUGIN_ROOT = os.environ.get("CLAUDE_PLUGIN_ROOT", os.path.join(os.path.dirname(__file__), ".."))
if PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, PLUGIN_ROOT)

from lib.policy import evaluate_account_policy
from lib.resolve_allowed_emails import resolve_allowed_emails


def _read_auth_email() -> str | None:
    """Run `claude auth status` and return the email, or None on any failure."""
    try:
        result = subprocess.run(
            ["claude", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        if not data.get("loggedIn"):
            return None
        return data.get("email") or None
    except Exception:
        return None


def _read_account_guard_config() -> dict | None:
    """Read accountGuard section from ~/.claude/settings.json, or None if absent/unreadable."""
    settings_path = os.path.expanduser("~/.claude/settings.json")
    try:
        with open(settings_path) as f:
            settings = json.load(f)
        config = settings.get("accountGuard")
        return config if isinstance(config, dict) else None
    except Exception:
        return None


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    cwd = payload.get("cwd") or os.getcwd()

    config = _read_account_guard_config()
    if config is None:
        # Plugin not configured — stay silent.
        sys.exit(0)

    on_mismatch = config.get("onMismatch", "warn")
    expected_by_folder = config.get("expectedByFolder")
    global_allowed = config.get("allowedEmails")

    resolved = resolve_allowed_emails(global_allowed, expected_by_folder, cwd)

    if not resolved.allowed_emails:
        # No policy applies to this directory.
        sys.exit(0)

    email = _read_auth_email()
    policy = evaluate_account_policy(email, resolved.allowed_emails)

    if policy.level == "ok":
        sys.exit(0)

    folder_hint = (
        f" (matched rule: {resolved.matched_folder_key})" if resolved.matched_folder_key else ""
    )
    allowed_str = ", ".join(resolved.allowed_emails)
    message = (
        f"Account Guard{folder_hint}: {policy.reason} "
        f"Expected: {allowed_str}. "
        f"Switch accounts or update ~/.claude/settings.json."
    )

    if on_mismatch == "block":
        print(message, file=sys.stderr)
        sys.exit(2)
    else:
        # warn (default): inject as system message so Claude sees it too
        payload = {"systemMessage": f"[Account Guard] {policy.reason} Expected: {allowed_str}."}
        print(json.dumps(payload))
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never block the user due to plugin errors.
        sys.exit(0)
