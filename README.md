# account-guard

A Claude Code plugin that warns or blocks prompts when the active Claude account doesn't match the expected account for the current directory.

Useful for teams or individuals who switch between work and personal Claude accounts and want a guardrail against accidentally using the wrong one.

## Installation

```
/plugin marketplace add fseitun/claude-account-guard
/plugin install account-guard@fseitun
```

## Configuration

**`on_mismatch`** — set at install time when prompted, or via `/plugin config`. Options: `warn` (default) or `block`. You can also set `onMismatch` directly in `~/.claude/account-guard.json` (camelCase) if you prefer manual config.

**Folder policy** is configured in `~/.claude/account-guard.json`:

```json
{
  "expectedByFolder": {
    "~/work/acme":    { "allowedEmails": ["you@acme.com"] },
    "~/personal":     { "allowedEmails": ["you@gmail.com"] }
  }
}
```

**`expectedByFolder`** — map of directory prefixes to allowed email lists. The longest matching prefix wins. Paths support `~`.

**`allowedEmails`** (optional, top-level) — a global allowed list that applies everywhere regardless of directory.

## Commands

**`/account-status [path]`** — shows the active Claude account and evaluates the policy for the given path (or current directory).

## How it works

On every `UserPromptSubmit`, the hook:
1. Gets the current working directory from the hook payload
2. Finds the longest-prefix match in `expectedByFolder`
3. Runs `claude auth status` to get the active email
4. Warns or blocks if the email isn't in the matched rule's allowed list

If no config is present, or no rule matches the current directory, the hook is silent.

## Development

```bash
# Run tests
python3 -m unittest discover tests/ -v

# Test the hook manually
echo '{"cwd": "/your/path", "session_id": "test", "hook_event_name": "UserPromptSubmit", "user_prompt": "hello"}' \
  | CLAUDE_PLUGIN_ROOT=$(pwd) python3 hooks/account_guard_hook.py
echo "exit: $?"
```
