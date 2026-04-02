"""Resolve which allowed-emails list applies to the current working directory."""

import os
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class ResolveResult:
    allowed_emails: list[str] = field(default_factory=list)
    source_hint: Literal["settings", "expectedByFolder", "none"] = "none"
    matched_folder_key: str | None = None


def normalize_allowed_emails(raw: list | None) -> list[str]:
    if not raw or not isinstance(raw, list):
        return []
    return [s for s in (str(e).strip() for e in raw) if s]


def _normalize_path(p: str) -> str:
    expanded = os.path.expanduser(p)
    normalized = os.path.normpath(expanded)
    if len(normalized) > 1 and normalized.endswith(os.sep):
        normalized = normalized[:-1]
    return normalized


def longest_prefix_folder_key(workspace_path: str, keys: list[str]) -> str | None:
    if not keys:
        return None

    ws = _normalize_path(workspace_path)
    best: str | None = None
    best_len = -1

    for key in keys:
        k = _normalize_path(key)
        if ws == k or ws.startswith(k + os.sep):
            if len(k) > best_len:
                best = key
                best_len = len(k)

    return best


def resolve_allowed_emails(
    merged_allowed_emails: list | None,
    expected_by_folder: dict | None,
    workspace_path: str | None,
) -> ResolveResult:
    merged = normalize_allowed_emails(merged_allowed_emails)
    if merged:
        return ResolveResult(allowed_emails=merged, source_hint="settings")

    if not workspace_path or not expected_by_folder or not isinstance(expected_by_folder, dict):
        return ResolveResult()

    match_key = longest_prefix_folder_key(workspace_path, list(expected_by_folder.keys()))
    if not match_key:
        return ResolveResult()

    entry = expected_by_folder.get(match_key) or {}
    emails = normalize_allowed_emails(entry.get("allowedEmails"))
    return ResolveResult(
        allowed_emails=emails,
        source_hint="expectedByFolder",
        matched_folder_key=match_key,
    )
