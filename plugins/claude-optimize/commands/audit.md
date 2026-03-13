---
description: Full environment health check with scored dimensions
argument-hint: "[focus-dimension]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash(python3:*)
  - Agent
  - AskUserQuestion
---

# Optimize: Audit

Arguments: `$ARGUMENTS`

You are the Claude Optimize auditor. Perform a comprehensive health check of this Claude Code environment.

## Workflow

### Phase 1: Gather Data

**CRITICAL: You MUST NOT run any Bash commands or python3 scripts during Phase 1.** ALL analysis is performed by the agents below. Your ONLY tool in Phase 1 is the Agent tool with the exact `subagent_type` values shown. Do NOT run `ls`, `find`, `cat`, `wc`, `python3`, or any other commands yourself.

Launch these 4 Agent calls **simultaneously in a single response** using the exact `subagent_type` values:

1. **Security & Permissions** — `subagent_type: "claude-optimize:security-scanner"`. Returns security_posture score (0-100) and key findings covering permissions, deny rules, MCP trust, hook security, prompt injection.

2. **Context Efficiency** — `subagent_type: "claude-optimize:context-measurer"`. Returns context_efficiency score (0-100) and key findings covering CLAUDE.md token load, skill descriptions, MCP tool count, compaction resilience.

3. **Hooks, Memory & MCP** — `subagent_type: "claude-optimize:hooks-memory-mcp-analyzer"`. Returns hook_coverage, memory_hygiene, and mcp_health scores (each 0-100) and key findings.

4. **Codebase & Skills** — `subagent_type: "claude-optimize:codebase-skills-analyzer"`. Returns codebase_alignment, skill_quality, and claude_md_quality scores (each 0-100) and key findings.

If session logs exist, also launch a session-analyzer agent (general-purpose) to extract usage patterns. This is optional — proceed without it if no logs are found.

### Phase 2: Score All Dimensions

ALWAYS use the bundled score aggregation script. Do NOT calculate weighted scores manually.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score_aggregator.py --scores '{"claude_md_quality": XX, "security_posture": XX, "context_efficiency": XX, "hook_coverage": XX, "skill_quality": XX, "memory_hygiene": XX, "mcp_health": XX, "codebase_alignment": XX}' --json
```

Reference weights:

| Dimension | Weight | Source |
|-----------|--------|--------|
| CLAUDE.md Quality | 20% | claude-md-manager score |
| Security Posture | 20% | security-auditor score |
| Context Efficiency | 15% | context-optimizer score |
| Hook Health | 10% | hook-recommender score |
| Skill Coverage | 10% | skill inventory analysis |
| Memory Hygiene | 10% | memory-manager score |
| MCP Configuration | 10% | mcp-advisor score |
| Plugin Health | 5% | load time, conflicts |

**Overall Score** = weighted sum of all dimensions

**Grade**: A (90-100), B (80-89), C (70-79), D (60-69), F (<60)

### Phase 3: Generate Report

```markdown
## Environment Audit Report

**Overall Grade**: [GRADE] ([score]/100)
**Date**: [date]

### Dimension Scores
| Dimension | Score | Grade | Key Issue |
|-----------|-------|-------|-----------|
| CLAUDE.md Quality | XX/100 | [grade] | [brief] |
| Security Posture | XX/100 | [grade] | [brief] |
| Context Efficiency | XX/100 | [grade] | [brief] |
| Hook Health | XX/100 | [grade] | [brief] |
| Skill Coverage | XX/100 | [grade] | [brief] |
| Memory Hygiene | XX/100 | [grade] | [brief] |
| MCP Configuration | XX/100 | [grade] | [brief] |
| Plugin Health | XX/100 | [grade] | [brief] |

### Prioritized Recommendations
| # | Priority | Dimension | Action | Impact |
|---|----------|-----------|--------|--------|
| 1 | Critical | [dim] | [specific action] | +X points |
| 2 | High | [dim] | [specific action] | +X points |
...

### Quick Wins (Easy, High Impact)
[List actions that are simple to implement with high score improvement]

### Deep Dives Needed
[List dimensions that need focused attention via specific /optimize: commands]
```

### Phase 4: Present and Offer Next Steps

Present the report and ask:
**"Would you like me to address any of these recommendations? You can also run specific modes for deeper analysis:**
- `/optimize:security` for detailed security hardening
- `/optimize:context` for token optimization
- `/optimize:hooks` for hook improvements
- `/optimize:loop` for autonomous multi-pass optimization"

## Rules

1. NEVER modify files during audit - this is read-only analysis
2. **You MUST NOT run any Bash/python3 commands in Phase 1** — use ONLY the Agent tool with the exact subagent_types listed above
3. **The ONLY Bash command you run directly is `score_aggregator.py` in Phase 2** — everything else is delegated to agents
4. Be specific in recommendations - cite exact files, line numbers, and values
5. Prioritize recommendations by impact (score improvement) and effort (ease of implementation)
6. If a dimension can't be scored (e.g., no session logs), note it as "N/A" with explanation
