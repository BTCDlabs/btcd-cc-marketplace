---
name: session-analyzer
description: >
  Use when running /optimize:audit, /optimize:skills, /optimize:hooks, or /optimize:discover
  to analyze recent Claude Code session logs for tool usage patterns, error frequency,
  repeated workflows, and automation opportunities. Do NOT trigger on general coding tasks.
---

# Session Analyzer

Analyzes recent Claude Code session logs (JSONL format) to extract usage patterns, identify automation opportunities, and detect recurring errors. Powers data-driven recommendations across multiple optimize modes.

## Finding Session Logs

Session logs are stored in the project-specific Claude directory:

```
~/.claude/projects/
```

Use Glob to find the project directory matching the current working directory, then find `*.jsonl` files within it. Sort by modification time and analyze up to 30 most recent sessions. For `/optimize:discover`, at least 15 sessions are needed for bloat detection. For other modes, 10 sessions is sufficient.

## Analysis Method

**ALWAYS use the bundled script** — it extracts all metrics needed by discover, audit, skills, and hooks modes. Do NOT write your own analysis scripts or inline Python. The bundled script covers all required metrics.

```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/session-analyzer/scripts/analyze_sessions.py --max-sessions 30
```

The script auto-detects the project directory from the current working directory. To override:
```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/session-analyzer/scripts/analyze_sessions.py --project-dir <path> --max-sessions 30
```

The script outputs 14 structured sections: tool usage, bash commands (base + full), file edits, file reads, glob/grep patterns, MCP tool calls, ToolSearch queries, error patterns, branches, workflow bigrams/trigrams, and session distribution.

## Key Metrics to Extract

### Tool Usage Frequency
Which tools are used most? High Read/Grep usage suggests exploration-heavy work. High Edit/Write suggests active development. High Bash usage suggests CLI-heavy workflows.

### Bash Command Patterns
Commands run 5+ times across sessions with similar arguments are automation candidates. Look for:
- Build commands (npm run, cargo build, make)
- Test commands (npm test, pytest, cargo test)
- Lint/format commands (eslint, prettier, black)
- Git workflows (git log, git diff, git stash)

### File Edit Frequency
Files edited most frequently suggest:
- Hot paths that need better tooling
- Files that might benefit from specialized skills
- Common modification patterns

### Error Patterns
Recurring errors suggest:
- Missing hooks that could prevent mistakes
- Incorrect assumptions in CLAUDE.md
- Missing deny rules for dangerous operations

### Session Duration and Complexity
Approximate from first-to-last timestamps. Long sessions may indicate complex tasks that could benefit from decomposition or specialized agents.

## Output Format

```markdown
## Session Analysis Report

**Sessions analyzed**: [count]
**Date range**: [oldest] to [newest]

### Tool Usage (Top 10)
| Tool | Count | % of Total |
|------|-------|------------|
| Read | XXX | XX% |
| Edit | XXX | XX% |
| ... | ... | ... |

### Bash Commands (Top 10)
| Command | Count | Automation Candidate? |
|---------|-------|-----------------------|
| npm test | XX | Yes - hook or skill |
| git diff | XX | No - exploratory |
| ... | ... | ... |

### Most Edited Files (Top 10)
| File | Edit Count | Pattern |
|------|------------|---------|
| src/api/routes.ts | XX | Active development |
| ... | ... | ... |

### Error Summary
| Error Type | Count | Suggested Fix |
|------------|-------|---------------|
| [pattern] | XX | [hook/skill/config] |

### Automation Opportunities
1. [Specific opportunity with evidence]
2. [Specific opportunity with evidence]
```
