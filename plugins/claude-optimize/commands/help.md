---
description: Show all optimize modes and usage
allowed-tools: Read
---

# Claude Optimize - Help

Display the following help information to the user:

## Available Modes

| Command | Purpose |
|---------|---------|
| `/optimize:init` | First-run setup for a new repo - detects project type, creates CLAUDE.md, sets up security guardrails |
| `/optimize:audit` | Full environment health check - scores CLAUDE.md quality, hook health, permissions, memory hygiene |
| `/optimize:security` | Security hardening - audits permissions, MCP servers, deny rules, prompt injection vectors |
| `/optimize:context` | Token/context optimization - reduces CLAUDE.md bloat, skill description sizes, MCP tool count |
| `/optimize:skills` | Skill lifecycle management - inventories skills, checks trigger quality, identifies gaps |
| `/optimize:hooks` | Hook analysis - lists hooks with timing, detects missing hooks, recommends new ones |
| `/optimize:memory` | Memory hygiene - scores entries for staleness, identifies migration candidates, deduplicates |
| `/optimize:mcp` | MCP server management - health checks, security audit, stack-based recommendations |
| `/optimize:report` | Comprehensive report - runs all dimension analyses and generates scored summary |
| `/optimize:loop` | Guided autonomous optimization - runs report, gets approval, iterates until targets met |
| `/optimize:discover` | Reflect on usage patterns to discover new capabilities and prune unused ones |

## Quick Start

1. **New repo?** Start with `/optimize:init`
2. **Existing setup?** Run `/optimize:audit` for a health check
3. **Security review?** Use `/optimize:security`
4. **Full optimization?** Use `/optimize:report` then `/optimize:loop`
5. **Expand capabilities?** Run `/optimize:discover` to find what's missing

## Scoring System

Each mode contributes to a weighted score across 8 dimensions:

| Dimension | Weight | Key Metrics |
|-----------|--------|-------------|
| CLAUDE.md Quality | 20% | Token count, instruction density, completeness |
| Security Posture | 20% | Deny rules, MCP trust, permission breadth |
| Context Efficiency | 15% | Total token load, skill sizes, MCP tool count |
| Hook Health | 10% | Coverage, error rate, timeout risk |
| Skill Coverage | 10% | Trigger quality, overlap, gap analysis |
| Memory Hygiene | 10% | Staleness, duplicates, migration candidates |
| MCP Configuration | 10% | Connectivity, security, relevance |
| Plugin Health | 5% | Load time, conflict detection |

**Grades**: A (90-100), B (80-89), C (70-79), D (60-69), F (<60)

## Usage

```
/optimize:audit                    # Run audit mode
/optimize:security                 # Run security analysis
/optimize:loop --max-iterations 10 # Autonomous optimization
```

All modes present findings first and require approval before making changes.
