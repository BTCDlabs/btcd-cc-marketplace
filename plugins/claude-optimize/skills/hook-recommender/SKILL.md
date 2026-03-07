---
name: hook-recommender
description: >
  Use when running /optimize:hooks to analyze existing hooks for health issues,
  detect missing hooks based on project type, and recommend new hooks with implementations.
  Triggers on hook analysis, hook creation for optimization, or hook health checking.
  Do NOT trigger on general hook development or coding tasks.
---

# Hook Recommender

Analyzes Claude Code hook configuration for health, coverage gaps, and improvement opportunities. Powers `/optimize:hooks` and the hook health dimension of `/optimize:audit`.

## Analysis Workflow

### Step 1: Inventory Existing Hooks

Read hook configuration from:
- `.claude/settings.json` (project hooks)
- `.claude/settings.local.json` (personal hooks)
- Any plugin hooks (from installed plugins)

For each hook, record:
- Event type (PreToolUse, PostToolUse, Stop, SessionStart, etc.)
- Matcher pattern
- Command/script path
- Timeout setting

### Step 2: Hook Health Assessment

For each hook:

#### Timeout Risk
- No timeout set: Warning (defaults may be too long)
- Timeout > 30s: Warning (blocks Claude for too long)
- Timeout > 5s: Info (consider if this is necessary)
- Timeout <= 5s: OK

#### Error Detection
Check hook scripts for common issues:
- Missing shebang (`#!/bin/bash` or `#!/usr/bin/env bash`)
- Missing `set -euo pipefail`
- Unquoted variables in commands (injection risk)
- Missing executable permission
- References to non-existent files
- Syntax errors (run `bash -n <script>` for bash scripts)

#### Functionality Test
For each hook script:
- Does the script exist at the referenced path?
- Is it executable?
- Does it handle stdin properly (for hooks that receive JSON input)?
- Does it produce valid output format (JSON for blocking hooks)?

### Step 3: Coverage Analysis

Based on detected project type (from codebase-analyzer), identify missing hooks:

Reference: `${CLAUDE_PLUGIN_ROOT}/skills/hook-recommender/references/hook-patterns.md`

#### Essential Hooks (All Projects)
| Hook | Event | Purpose |
|------|-------|---------|
| Sensitive file protection | PreToolUse (Write\|Edit) | Block writes to .env, .key, credential files |
| Dangerous command blocker | PreToolUse (Bash) | Block rm -rf /, chmod 777, etc. |

#### Language-Specific Hooks
| Detected | Hook | Event | Purpose |
|----------|------|-------|---------|
| TypeScript/JS | Auto-format | PostToolUse (Write\|Edit) | Run prettier/eslint --fix |
| Python | Auto-format | PostToolUse (Write\|Edit) | Run black/ruff format |
| Rust | Auto-format | PostToolUse (Write\|Edit) | Run cargo fmt |
| Go | Auto-format | PostToolUse (Write\|Edit) | Run gofmt |
| Any with tests | Test runner | PostToolUse (Write\|Edit) | Run relevant tests |

#### Workflow Hooks
| Hook | Event | Purpose |
|------|-------|---------|
| PreCompact context saver | PreCompact | Preserve critical info during compaction |
| Commit message enforcer | PreToolUse (Bash) | Enforce conventional commits |
| Branch protection | PreToolUse (Bash) | Prevent direct commits to main |

### Step 4: Session Log Analysis

If session logs are available, look for:
- Repeated manual formatting commands -> suggest auto-format hook
- Repeated test runs after edits -> suggest auto-test hook
- Repeated mistakes Claude makes -> suggest prevention hook
- Commands that frequently fail -> suggest validation hook

### Step 5: Generate Report

```markdown
## Hook Health Report

**Overall Grade**: [A-F] ([score]/100)

### Existing Hooks ([count])
| # | Event | Matcher | Timeout | Health |
|---|-------|---------|---------|--------|
| 1 | PreToolUse | Write | 10s | OK |
| 2 | PostToolUse | Bash | none | Warning |

### Health Issues
| Hook | Issue | Severity | Fix |
|------|-------|----------|-----|
| [#] | [description] | [level] | [action] |

### Missing Hooks (Recommended)
| Hook | Event | Priority | Rationale |
|------|-------|----------|-----------|
| .env protection | PreToolUse | Critical | No credential file protection |
| Auto-format | PostToolUse | High | [formatter] detected but no hook |

### Recommended Implementations
[For each missing hook, provide ready-to-use JSON config and script]

### Automation Opportunities (from session analysis)
| Pattern | Frequency | Suggested Hook |
|---------|-----------|---------------|
| [pattern] | [count] | [hook type] |
```

## Scoring Contribution

Hook health dimension (10% of total score):
- Essential hooks present: 40 points
- Hook health (no errors/warnings): 30 points
- Language-specific hooks: 20 points
- Workflow hooks: 10 points
