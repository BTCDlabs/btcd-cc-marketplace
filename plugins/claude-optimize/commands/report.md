---
description: Comprehensive scored report across all dimensions
argument-hint: "[focus-dimensions]"
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(python3:*)
  - Agent
---

# Optimize: Report

Arguments: `$ARGUMENTS`

You are the Claude Optimize report generator. Create a comprehensive optimization report covering all dimensions.

## Workflow

### Phase 1: Parallel Data Collection

Launch these Agent calls **simultaneously in a single response** (do NOT use loops or sequential calls):

1. **Agent: Security & Permissions** — Use the security-auditor skill to analyze permissions, deny rules, MCP security. Return a score (0-100) and key findings.

2. **Agent: Context & CLAUDE.md** — Use the context-optimizer and claude-md-manager skills to measure token efficiency and CLAUDE.md quality. Return scores for both dimensions and key findings.

3. **Agent: Hooks, Memory & MCP** — Use the hook-recommender, memory-manager, and mcp-advisor skills to check hook health, memory hygiene, and MCP configuration. Return scores for all three and key findings.

4. **Agent: Codebase & Skills** — Use the codebase-analyzer skill to detect project type, then inventory skills and assess coverage. Return scores for plugin health and skill coverage.

### Phase 2: Aggregate and Score

Once all agents return, use the bundled score aggregation script. Do NOT calculate weighted scores manually.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score_aggregator.py --scores '{"claude_md_quality": XX, "security_posture": XX, "context_efficiency": XX, "hook_coverage": XX, "skill_quality": XX, "memory_hygiene": XX, "mcp_health": XX, "codebase_alignment": XX}' --json
```

Replace XX values with the scores returned from each agent. The script uses default weights:

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

**Grade**: A (90-100), B (80-89), C (70-79), D (60-69), F (<60)

### Phase 3: Present Report

```markdown
# Claude Code Optimization Report

**Project**: [repo name]
**Date**: [date]
**Overall Grade**: [GRADE] ([score]/100)

---

## Executive Summary

[2-3 sentences summarizing the environment health and top priorities]

---

## Dimension Scores

| Dimension | Weight | Score | Grade | Trend |
|-----------|--------|-------|-------|-------|
| CLAUDE.md Quality | 20% | XX | [grade] | -- |
| Security Posture | 20% | XX | [grade] | -- |
| Context Efficiency | 15% | XX | [grade] | -- |
| Hook Health | 10% | XX | [grade] | -- |
| Skill Coverage | 10% | XX | [grade] | -- |
| Memory Hygiene | 10% | XX | [grade] | -- |
| MCP Configuration | 10% | XX | [grade] | -- |
| Plugin Health | 5% | XX | [grade] | -- |
| **Weighted Total** | 100% | **XX** | **[grade]** | |

---

## Detailed Findings

### CLAUDE.md Quality (XX/100)
[Detailed findings from claude-md-manager]

### Security Posture (XX/100)
[Detailed findings from security-auditor]

### Context Efficiency (XX/100)
[Detailed findings from context-optimizer]

### Hook Health (XX/100)
[Detailed findings from hook-recommender]

### Skill Coverage (XX/100)
[Skill inventory and trigger quality analysis]

### Memory Hygiene (XX/100)
[Detailed findings from memory-manager]

### MCP Configuration (XX/100)
[Detailed findings from mcp-advisor]

### Plugin Health (XX/100)
[Plugin load time and conflict analysis]

---

## Action Plan

### Critical (Do Now)
1. [action] - [dimension] - estimated +X points

### High Priority (This Week)
1. [action] - [dimension] - estimated +X points

### Medium Priority (This Month)
1. [action] - [dimension] - estimated +X points

### Low Priority (When Time Allows)
1. [action] - [dimension] - estimated +X points

---

## Recommended Next Steps

- `/optimize:security` - [if security score < 80]
- `/optimize:context` - [if context score < 80]
- `/optimize:hooks` - [if hook score < 80]
- `/optimize:loop --max-iterations 10` - [for autonomous improvement]
```

## Rules

1. This is a READ-ONLY report - do not modify any files
2. Score every dimension, even if data is limited (note limitations)
3. Be specific in action items - cite files, patterns, and values
4. Prioritize actions by impact (score improvement) and effort
5. Do NOT use the TodoWrite tool for tracking progress
6. Launch all Agent calls in a single parallel response — never use loops or sequential dispatching
