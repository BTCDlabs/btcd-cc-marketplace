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

**CRITICAL: You MUST NOT run any Bash commands or python3 scripts during Phase 1.** ALL analysis is performed by the agents below. Your ONLY tool in Phase 1 is the Agent tool. Do NOT run `ls`, `find`, `cat`, `python3`, or any other commands yourself.

Launch these 4 Agent calls **simultaneously in a single response** using the exact `subagent_type` values shown:

1. **Security & Permissions** — `subagent_type: "claude-optimize:security-scanner"`. In your prompt to the agent, include these EXACT commands for it to run (copy them verbatim — the agent cannot discover paths on its own):
   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/permission_auditor.py --json --summary
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/mcp_health_check.py --json --summary
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/hook_validator.py --settings .claude/settings.json --json --summary
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/prompt_injection_scanner.py --auto-discover --json --summary
   ```
   Ask it to return a security_posture score (0-100) and key findings.

2. **Context Efficiency** — `subagent_type: "claude-optimize:context-measurer"`. In your prompt to the agent, include these EXACT commands for it to run (copy them verbatim):
   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/token_counter.py --claude-md --json --summary
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skill_analyzer.py --auto-discover --json --summary
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/mcp_health_check.py --json --summary
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/permission_auditor.py --json --summary
   ```
   Ask it to return a context_efficiency score (0-100) and key findings.

3. **Hooks, Memory & MCP** — `subagent_type: "claude-optimize:hooks-memory-mcp-analyzer"`. In your prompt to the agent, include these EXACT commands for it to run (copy them verbatim):
   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/env_inventory.py --json --summary
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/hook_validator.py --settings .claude/settings.json --json --summary
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/memory_staleness.py --json --summary
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/mcp_health_check.py --json --summary
   ```
   Ask it to return hook_coverage, memory_hygiene, and mcp_health scores (each 0-100) and key findings.

4. **Codebase & Skills** — `subagent_type: "claude-optimize:codebase-skills-analyzer"`. In your prompt to the agent, include these EXACT commands for it to run (copy them verbatim):
   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/codebase_detector.py --json
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skill_analyzer.py --auto-discover --json --summary
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/claude_md_validator.py --json --summary
   ```
   Ask it to return codebase_alignment, skill_quality, and claude_md_quality scores (each 0-100) and key findings.

### Phase 2: Aggregate and Score

Once all agents return, use the bundled score aggregation script. Run commands EXACTLY as shown — do NOT append `2>&1`, pipe through Python, add shell redirects, or modify commands in any way. Do NOT calculate weighted scores manually.

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
2. **You MUST NOT run any Bash/python3 commands in Phase 1** — use ONLY the Agent tool with the exact subagent_types listed above
3. **The ONLY Bash command you run directly is `score_aggregator.py` in Phase 2** — everything else is delegated to agents
4. Score every dimension, even if data is limited (note limitations)
5. Be specific in action items - cite files, patterns, and values
6. Prioritize actions by impact (score improvement) and effort
7. Do NOT use the TodoWrite tool for tracking progress
8. Launch all 4 Agent calls in a single parallel response — never use loops or sequential dispatching
