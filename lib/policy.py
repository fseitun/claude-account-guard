"""Policy evaluation: is the current account allowed?"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class PolicyResult:
    level: Literal["ok", "warning", "error"]
    reason: str = ""


def evaluate_account_policy(
    email: str | None,
    allowed_emails: list[str],
) -> PolicyResult:
    if not email or not email.strip():
        return PolicyResult(
            level="warning",
            reason="Not logged in to Claude (no email found).",
        )

    norm = email.strip().lower()
    allowed = [e.strip().lower() for e in allowed_emails if e.strip()]

    if allowed and norm not in allowed:
        return PolicyResult(
            level="error",
            reason=f"Logged in as {norm}, which is not in the allowed list for this directory.",
        )

    return PolicyResult(level="ok")
