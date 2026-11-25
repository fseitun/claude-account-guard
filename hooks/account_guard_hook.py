#!/usr/bin/env python3
"""UserPromptSubmit hook: enforce per-folder Claude account policy."""

import json
import os
import subprocess
import sys

PLUGIN_ROOT = os.environ.get("CLAUDE_PLUGIN_ROOT", os.path.join(os.path.dirname(__file__), ".."))
if PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, PLUGIN_ROOT)

from lib.auth_status import AuthStatus, parse_auth_status
from lib.policy import evaluate_account_policy
from lib.resolve_allowed_emails import resolve_allowed_emails


def _read_auth_status() -> AuthStatus:
    """Run `claude auth status`; never raises."""
    try:
        result = subprocess.run(
            ["claude", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        return AuthStatus(state="unknown", detail="`claude` is not on PATH for hooks.")
    except subprocess.TimeoutExpired:
        return AuthStatus(state="unknown", detail="`claude auth status` timed out.")
    except Exception as e:
        return AuthStatus(state="unknown", detail=f"`claude auth status` failed: {e}")
    return parse_auth_status(result.returncode, result.stdout)


def _warn(text: str) -> None:
    """Show `text` to the user (systemMessage) and to Claude (additionalContext)."""
    print(
        json.dumps(
            {
                "systemMessage": text,
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": text,
                },
            }
        )
    )
    sys.exit(0)


def _read_account_guard_config() -> dict | None:
    """Read config from ~/.claude/account-guard.json, or None if absent/unreadable."""
    config_path = os.path.expanduser("~/.claude/account-guard.json")
    try:
        with open(config_path) as f:
            config = json.load(f)
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

    on_mismatch = (
        str(
            os.environ.get("CLAUDE_PLUGIN_OPTION_ON_MISMATCH") or config.get("onMismatch") or "warn"
        )
        .strip()
        .lower()
    )
    expected_by_folder = config.get("expectedByFolder")
    global_allowed = config.get("allowedEmails")

    resolved = resolve_allowed_emails(global_allowed, expected_by_folder, cwd)

    if not resolved.allowed_emails:
        # No policy applies to this directory.
        sys.exit(0)

    allowed_str = ", ".join(resolved.allowed_emails)

    status = _read_auth_status()
    if status.state == "unknown":
        # We could not tell who is logged in: always warn, never block, even in block mode.
        _warn(
            f"[Account Guard] Could not check the active Claude account ({status.detail}) "
            f"Expected: {allowed_str}."
        )

    policy = evaluate_account_policy(status.email, resolved.allowed_emails)

    if policy.level == "ok":
        sys.exit(0)

    folder_hint = (
        f" (matched rule: {resolved.matched_folder_key})" if resolved.matched_folder_key else ""
    )
    message = (
        f"Account Guard{folder_hint}: {policy.reason} "
        f"Expected: {allowed_str}. "
        f"Switch accounts or update ~/.claude/account-guard.json."
    )

    if on_mismatch == "block":
        print(message, file=sys.stderr)
        sys.exit(2)
    else:
        # warn (default): systemMessage alone reaches only the user, so also add context for Claude.
        _warn(f"[Account Guard] {policy.reason} Expected: {allowed_str}.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never block the user due to plugin errors.
        sys.exit(0)
