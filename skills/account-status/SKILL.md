---
name: account-status
description: Show the currently active Claude account and evaluate the account-guard policy for the current (or specified) directory
argument-hint: [folder path]
allowed-tools: [Bash, Read]
---

# Account Status

Show the active Claude account and whether it satisfies the account-guard policy.

## Instructions

1. Run `claude auth status` and display the result in a readable format (email, org, subscription type, auth method).

2. Read `~/.claude/settings.json` and extract `accountGuard.expectedByFolder` (and `accountGuard.allowedEmails` if present).

3. If $ARGUMENTS is provided, use that as the path to evaluate; otherwise use the current working directory.

4. Find the longest-prefix match in `expectedByFolder` for the path (expand `~` before comparing).

5. Report:
   - Current account (email)
   - Matched rule key (or "no rule matched")
   - Allowed emails for that rule
   - Policy result: OK / WARNING / ERROR and the reason

Keep the output concise — one short section per step above.
