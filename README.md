# claude-account-guard

A Claude Code plugin that warns or blocks prompts when the active Claude account doesn't match the expected account for the current directory.

Useful for teams or individuals who switch between work and personal Claude accounts and want a guardrail against accidentally using the wrong one.

## Installation

```
/plugin install https://github.com/fseitun/claude-account-guard
```

## Configuration

Add an `accountGuard` section to `~/.claude/settings.json`:

```json
{
  "accountGuard": {
    "onMismatch": "warn",
    "expectedByFolder": {
      "~/work/acme":    { "allowedEmails": ["you@acme.com"] },
      "~/personal":     { "allowedEmails": ["you@gmail.com"] }
    }
  }
}
```

### Options

**`onMismatch`** — what to do when the active account isn't in the allowed list:
- `"warn"` (default) — injects a warning into Claude's context before the prompt is processed; you can still continue
- `"block"` — blocks the prompt entirely with an error message

**`expectedByFolder`** — map of directory prefixes to allowed email lists. The longest matching prefix wins. Paths support `~`.

**`allowedEmails`** (optional, top-level) — a global allowed list that overrides `expectedByFolder` everywhere.

## Commands

**`/account-status [path]`** — shows the active Claude account and evaluates the policy for the given path (or current directory).

## How it works

On every `UserPromptSubmit`, the hook:
1. Gets the current working directory from the hook payload
2. Finds the longest-prefix match in `expectedByFolder`
3. Runs `claude auth status` to get the active email
4. Warns or blocks if the email isn't in the matched rule's allowed list

If no `accountGuard` config is present, or no rule matches the current directory, the hook is silent.

## Development

```bash
# Run tests
python3 -m unittest discover tests/ -v

# Test the hook manually
echo '{"cwd": "/your/path", "session_id": "test", "hook_event_name": "UserPromptSubmit", "user_prompt": "hello"}' \
  | CLAUDE_PLUGIN_ROOT=$(pwd) python3 hooks/account_guard_hook.py
echo "exit: $?"
```
