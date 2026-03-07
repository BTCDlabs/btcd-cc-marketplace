# claude-optimize

Meta-plugin for recursive self-improvement of Claude Code environments. Provides 10 optimization modes for analyzing and improving your Claude Code setup.

## Quick Start

```
/optimize:help     # See all available modes
/optimize:init     # First-run setup for a new repo
/optimize:audit    # Full environment health check
/optimize:report   # Comprehensive scored report
```

## Modes

| Command | Purpose |
|---------|---------|
| `/optimize:init` | First-run setup - detects project type, creates CLAUDE.md, sets up security |
| `/optimize:audit` | Full environment health check with scored dimensions |
| `/optimize:security` | Security hardening - permissions, deny rules, MCP trust |
| `/optimize:context` | Token/context optimization - reduce bloat, improve efficiency |
| `/optimize:skills` | Skill lifecycle - inventory, trigger quality, gap analysis |
| `/optimize:hooks` | Hook analysis - health, coverage, recommendations |
| `/optimize:memory` | Memory hygiene - staleness, duplicates, migration |
| `/optimize:mcp` | MCP server management - health, security, recommendations |
| `/optimize:report` | Comprehensive report across all dimensions |
| `/optimize:loop` | Guided autonomous optimization loop |

## Scoring System

Each mode contributes to a weighted score across 8 dimensions:

| Dimension | Weight |
|-----------|--------|
| CLAUDE.md Quality | 20% |
| Security Posture | 20% |
| Context Efficiency | 15% |
| Hook Health | 10% |
| Skill Coverage | 10% |
| Memory Hygiene | 10% |
| MCP Configuration | 10% |
| Plugin Health | 5% |

Grades: A (90-100), B (80-89), C (70-79), D (60-69), F (<60)

## Autonomous Loop

The `/optimize:loop` command runs a guided autonomous optimization cycle:

1. Runs a full report to get baseline scores
2. Presents prioritized plan for approval
3. Iterates through approved optimizations
4. Re-scores after each pass
5. Stops when targets are met or max iterations reached

```
/optimize:loop --max-iterations 10
/optimize:loop --completion-promise 'All scores above 80'
```

## Installation

### From the marketplace (if published)

Inside a Claude Code session:
```
/plugin install claude-optimize@claude-plugins-official
```

Or browse to it via `/plugin` > **Discover** tab.

### Local dev testing

Load the plugin directly for a single session:
```bash
claude --plugin-dir /path/to/claude-plugins-official/plugins/claude-optimize
```

### Verify installation

```
/optimize:help
```

## Design Principles

- **Read-first, write-with-approval**: All modes present findings before modifying anything
- **Self-contained**: No external plugin dependencies required
- **Composable**: Each mode is independent and focused
- **Security-first**: Security is a dedicated mode and part of every audit

## License

MIT
