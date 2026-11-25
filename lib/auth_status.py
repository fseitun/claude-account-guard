"""Interpret the output of `claude auth status`."""

import json
from dataclasses import dataclass
from typing import Literal


@dataclass
class AuthStatus:
    # "known": we know who is logged in (email may be None when logged out).
    # "unknown": we could not tell (CLI missing, timeout, unparseable output, no email).
    state: Literal["known", "unknown"]
    email: str | None = None
    detail: str = ""


def parse_auth_status(returncode: int | None, stdout: str) -> AuthStatus:
    """Parse `claude auth status` output.

    The CLI exits non-zero when logged out but still prints JSON with
    `"loggedIn": false`, so stdout is parsed regardless of the exit code.
    """
    try:
        data = json.loads(stdout)
    except (TypeError, ValueError):
        return AuthStatus(
            state="unknown",
            detail=f"`claude auth status` returned no usable output (exit {returncode}).",
        )
    if not isinstance(data, dict):
        return AuthStatus(state="unknown", detail="`claude auth status` returned unexpected JSON.")

    if data.get("loggedIn") is False:
        return AuthStatus(state="known", email=None)

    email = data.get("email")
    if data.get("loggedIn") and isinstance(email, str) and email.strip():
        return AuthStatus(state="known", email=email.strip())

    return AuthStatus(
        state="unknown",
        detail="`claude auth status` did not report an email for the active login.",
    )
