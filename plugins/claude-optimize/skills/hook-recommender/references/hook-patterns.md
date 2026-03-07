# Hook Patterns Reference

Common hook patterns organized by detection signal and purpose. Use web search for tools/frameworks not listed here.

## Auto-Formatting Hooks

| Detection Signal | Recommend | Event |
|-----------------|-----------|-------|
| `.prettierrc`, `prettier.config.js` | Prettier auto-format | PostToolUse (Write\|Edit) |
| `.eslintrc*`, `eslint.config.*` | ESLint auto-fix | PostToolUse (Write\|Edit) |
| `ruff.toml`, `pyproject.toml` with `[tool.ruff]` | Ruff format + lint | PostToolUse (Write\|Edit) |
| `pyproject.toml` with black/isort | Black + isort | PostToolUse (Write\|Edit) |
| `go.mod` | gofmt | PostToolUse (Write\|Edit) |
| `Cargo.toml` | rustfmt | PostToolUse (Write\|Edit) |
| `biome.json` | Biome format + lint | PostToolUse (Write\|Edit) |

## Type Checking Hooks

| Detection Signal | Recommend | Event |
|-----------------|-----------|-------|
| `tsconfig.json` | tsc --noEmit | PostToolUse (Write\|Edit) |
| `mypy.ini`, pyproject with mypy | mypy type check | PostToolUse (Write\|Edit) |
| `pyrightconfig.json` | pyright | PostToolUse (Write\|Edit) |

## Protection Hooks

| Detection Signal | Recommend | Event |
|-----------------|-----------|-------|
| `.env`, `.env.*` files | Block sensitive file edits | PreToolUse (Write\|Edit) |
| `credentials.*`, `secrets.*` | Block credential edits | PreToolUse (Write\|Edit) |
| Lock files (`*.lock`, `*-lock.*`) | Block direct lock file edits | PreToolUse (Write\|Edit) |
| `.git/` directory | Block git internal edits | PreToolUse (Write\|Edit) |

## Test Runner Hooks

| Detection Signal | Recommend | Event |
|-----------------|-----------|-------|
| `jest.config.*`, jest in package.json | Jest related tests | PostToolUse (Write\|Edit) |
| `vitest.config.*` | Vitest related tests | PostToolUse (Write\|Edit) |
| `pytest.ini`, conftest.py | pytest related tests | PostToolUse (Write\|Edit) |
| `Cargo.toml` + test files | cargo test | PostToolUse (Write\|Edit) |

## Notification Hooks

| Detection Signal | Recommend | Event |
|-----------------|-----------|-------|
| Any project | Permission prompt alert | Notification (permission_prompt) |
| Any project | Idle prompt alert | Notification (idle_prompt) |

### Available Notification Matchers

| Matcher | Triggers When |
|---------|---------------|
| `permission_prompt` | Claude needs permission for a tool |
| `idle_prompt` | Claude waiting for input (60+ seconds) |
| `auth_success` | Authentication succeeds |
| `elicitation_dialog` | MCP tool needs input |

### Example Notification Configuration

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "permission_prompt",
        "hooks": [
          {
            "type": "command",
            "command": "afplay /System/Library/Sounds/Ping.aiff"
          }
        ]
      },
      {
        "matcher": "idle_prompt",
        "hooks": [
          {
            "type": "command",
            "command": "osascript -e 'display notification \"Claude is waiting\" with title \"Claude Code\"'"
          }
        ]
      }
    ]
  }
}
```

## Workflow Hooks

| Purpose | Recommend | Event |
|---------|-----------|-------|
| Context preservation | Save critical info | PreCompact |
| Conventional commits | Enforce commit format | PreToolUse (Bash) matching git commit |
| Branch protection | Block commits to main | PreToolUse (Bash) matching git push |

## Hook Configuration Format

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "<formatter command> $CLAUDE_FILE_PATH",
            "timeout": 10
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'echo $CLAUDE_FILE_PATH | grep -qE \"\\.(env|key|pem)\" && echo {\"decision\":\"block\",\"reason\":\"Protected file\"} || true'",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

## Detection -> Recommendation Quick Reference

| If You See | Recommend This Hook |
|------------|-------------------|
| Prettier config | Auto-format on Edit/Write |
| ESLint config | Auto-lint on Edit/Write |
| Ruff/Black config | Auto-format Python |
| tsconfig.json | Type-check on Edit |
| Test directory | Run related tests on Edit |
| .env files | Block .env edits |
| Lock files | Block lock file edits |
| Go project | gofmt on Edit |
| Rust project | rustfmt on Edit |
| Multitasking | Notification hooks for alerts |
