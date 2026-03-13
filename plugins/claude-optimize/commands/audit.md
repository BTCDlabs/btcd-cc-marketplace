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

Do NOT run ad-hoc shell commands (`ls`, `find`, `cat`, `wc`, `jq`, etc.) to gather data. All analysis MUST go through bundled Python scripts or delegated skills/agents that use them.

Use the Agent tool to run independent dimension analyses in parallel where possible:

1. **Codebase Profile**: Use the **codebase-analyzer** skill to detect project type and Claude Code configuration status

2. **CLAUDE.md Quality**: Use the **claude-md-manager** skill to score all CLAUDE.md files using the quality rubric

3. **Security Posture**: Use the **security-auditor** skill to check permissions, deny rules, MCP security

4. **Context Efficiency**: Use the **context-optimizer** skill to measure token load across CLAUDE.md, skills, and MCP tools

5. **Memory Health**: Use the **memory-manager** skill to analyze memory file hygiene

6. **Session Patterns**: If session logs exist, use the **session-analyzer** skill to extract usage patterns

7. **Hook Health**: Use the **hook-recommender** skill to check existing hooks and identify missing ones

8. **MCP Configuration**: Use the **mcp-advisor** skill to health-check MCP servers

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
2. Be specific in recommendations - cite exact files, line numbers, and values
3. Prioritize recommendations by impact (score improvement) and effort (ease of implementation)
4. If a dimension can't be scored (e.g., no session logs), note it as "N/A" with explanation
