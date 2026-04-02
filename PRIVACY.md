# Privacy Policy

**Last updated: April 2, 2026**

## Overview

claude-account-guard is a Claude Code plugin that enforces account policies locally on your machine. It does not collect, transmit, or store any personal data.

## Data Processed

The plugin processes the following data **locally and transiently** on your machine:

- **Working directory path** — read from the Claude Code hook payload to match against your local policy rules.
- **Active Claude account email** — retrieved via `claude auth status` to compare against your configured allowed list.

Neither value is logged, stored, or sent anywhere. Both are used only in-memory during the hook execution to determine whether to warn or block the current prompt.

## Configuration Data

Policy rules you define under `accountGuard` in `~/.claude/settings.json` (folder paths and allowed email addresses) remain entirely on your machine and are never transmitted.

## Third-Party Services

This plugin does not integrate with any third-party services, analytics platforms, or remote APIs.

## Contact

For questions or concerns, open an issue at https://github.com/fseitun/claude-account-guard/issues.
