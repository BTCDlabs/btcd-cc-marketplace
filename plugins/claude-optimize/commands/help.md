---
description: Show all optimize modes and usage
allowed-tools: Read
---

# Claude Optimize - Help

First, read the plugin version from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and display it as a header. Then display the following help information:

**Claude Optimize v[version from plugin.json]**

## Available Modes

### Analysis (Read-Only)

These modes **never modify files**. They analyze your environment and report findings.

| Command | What It Does | When to Use | When NOT to Use |
|---------|-------------|-------------|-----------------|
| `/optimize:audit` | Quick scored health check across all 8 dimensions. Launches 4 parallel agents, returns a summary table with grades and top recommendations. | You want a fast overview of your environment's health. Good starting point after `/optimize:init`. | You want detailed per-dimension findings (use `/optimize:report`) or want to fix things (use specific modes below). |
| `/optimize:report` | Deep comprehensive report across all 8 dimensions. Same data collection as audit but produces detailed per-dimension findings, executive summary, and tiered action plan (critical/high/medium/low). | You want a thorough written report with specific findings, file references, and prioritized actions. | You just want a quick score (use `/optimize:audit`) or want to actually fix things (use specific modes). |
| `/optimize:security` | Focused security analysis — permission deny/allow rules, MCP server trust, hook script safety, prompt injection scanning. | You want to harden your security posture or investigate a specific security concern. | Your security score is already high and you want to improve other dimensions. |
| `/optimize:context` | Token budget analysis — CLAUDE.md size, skill description bloat, MCP tool count, compaction resilience. | Your context is getting large, sessions are slow, or compaction is losing important info. | You don't have a CLAUDE.md yet (use `/optimize:init` first). |
| `/optimize:skills` | Skill inventory and quality analysis — trigger descriptions, overlap detection, gap identification. | You want to understand what skills you have, whether they're well-described, or what's missing. | You want to create new skills (use `/optimize:discover` instead). |
| `/optimize:hooks` | Hook inventory and health — lists all hooks with timing, detects missing coverage, recommends new hooks. | You want to understand your hook setup or add automation for common workflows. | You don't have any hooks yet and want basic setup (use `/optimize:init`). |
| `/optimize:memory` | Memory file hygiene — staleness scoring, duplicate detection, CLAUDE.md migration candidates. | Your memory directory is growing and you want to clean it up or reorganize. | You don't use Claude Code memory files. |
| `/optimize:mcp` | MCP server health — connectivity checks, security assessment, stack-based recommendations. | You use MCP servers and want to verify health, security, or find useful new ones. | You don't use MCP servers. |

### Setup & Action

These modes **may modify files** (always with your approval first).

| Command | What It Does | When to Use | When NOT to Use |
|---------|-------------|-------------|-----------------|
| `/optimize:init` | First-run setup — detects project type, creates/improves CLAUDE.md, sets up security deny rules. | You're setting up Claude Code in a new repo, or a repo that has never been optimized. | The repo already has a well-configured CLAUDE.md and security rules (run `/optimize:audit` to check). |
| `/optimize:loop` | Autonomous optimization — runs a report, asks for approval on each fix, iterates until score target is met or max iterations reached. | You want hands-off improvement and are willing to approve changes as they're proposed. | You want to understand your environment first (use `/optimize:audit` or `/optimize:report`). |
| `/optimize:discover` | Reflects on your recent session patterns to discover automation opportunities — suggests new skills, hooks, or MCP servers, and prunes unused ones. | You've been using Claude Code for a while and want to find what repetitive work could be automated. | You're new to Claude Code (use `/optimize:init` then `/optimize:audit` first). |

### Audit vs Report — Which One?

Both analyze the same 8 dimensions using the same scripts and agents. The difference is output depth:

- **`/optimize:audit`** = dashboard view. Scores table, top recommendations, quick wins. Fast to read.
- **`/optimize:report`** = full document. Executive summary, detailed per-dimension findings with file citations, tiered action plan with time horizons. Thorough but longer.

**Rule of thumb**: Use `audit` for regular check-ins, `report` when you need a complete picture or want to share findings.

## Quick Start

1. **New repo?** `/optimize:init` to set up, then `/optimize:audit` to see where you stand
2. **Existing setup?** `/optimize:audit` for a quick health check
3. **Security review?** `/optimize:security` for focused analysis
4. **Full optimization?** `/optimize:report` then `/optimize:loop` to fix things
5. **Expand capabilities?** `/optimize:discover` to find automation opportunities

## Scoring System

Each analysis mode contributes to a weighted score across 8 dimensions:

| Dimension | Weight | What's Measured |
|-----------|--------|-----------------|
| CLAUDE.md Quality | 20% | Token count, instruction density, valid commands/paths, completeness |
| Security Posture | 20% | Deny rules coverage, MCP trust model, permission breadth, hook safety |
| Context Efficiency | 15% | Total token load, skill description sizes, MCP tool count |
| Hook Health | 10% | Hook coverage for project type, script quality, error handling |
| Skill Coverage | 10% | Trigger description quality, overlap, gaps vs project needs |
| Memory Hygiene | 10% | Staleness, duplicates, migration candidates to CLAUDE.md |
| MCP Configuration | 10% | Server connectivity, security posture, relevance to stack |
| Plugin Health | 5% | Load time, conflict detection |

**Grades**: A (90-100), B (80-89), C (70-79), D (60-69), F (<60)

## Usage Examples

```
/optimize:init                     # Set up a new repo
/optimize:audit                    # Quick health check
/optimize:report                   # Detailed report
/optimize:security                 # Deep security analysis
/optimize:loop --max-iterations 10 # Autonomous optimization (max 10 passes)
/optimize:discover                 # Find automation opportunities
```

All modes present findings first and require your approval before making any changes.
