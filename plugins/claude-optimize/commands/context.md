---
description: Token/context optimization - reduce bloat and waste
argument-hint: "[focus-area]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash(python3:*)
  - AskUserQuestion
---

# Optimize: Context

Arguments: `$ARGUMENTS`

You are the Claude Optimize context efficiency analyzer. Reduce token consumption in this Claude Code environment.

## Workflow

Use the **context-optimizer** skill to perform all analysis:

### Phase 1: Measure Current Token Load

ALWAYS use the bundled scripts for measurement. Do NOT estimate tokens manually or write ad-hoc counting code.

```bash
# Measure CLAUDE.md token load
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/token_counter.py --claude-md --json --summary

# Analyze skill descriptions
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skill_analyzer.py --auto-discover --json

# Check MCP tool count and token impact
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/mcp_health_check.py --json
```

Also check for PreCompact hook presence:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/permission_auditor.py --json
```
Review the `precompact_hook` field in the output.

Reference: `${CLAUDE_PLUGIN_ROOT}/skills/context-optimizer/references/compaction-strategies.md`

### Phase 2: Identify Reduction Opportunities

Use the CLAUDE.md validator to find stale references:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/claude_md_validator.py --auto-discover --json
```

The skill_analyzer output (Phase 1) already flags descriptions over 150 words and rates trigger quality. The mcp_health_check output (Phase 1) already flags excessive tool counts and shows which servers could benefit from deferred loading.

Additionally, Read each CLAUDE.md file and identify:
1. Redundant instructions (duplicates default Claude behavior)
2. Verbose content (paragraphs that could be bullet points)
3. Duplicate content (same info in multiple files)

### Phase 3: Generate Report

Present the context efficiency report from the context-optimizer skill, including:
- Current token usage breakdown
- Specific reduction opportunities with estimated savings
- Total recoverable tokens

### Phase 4: Offer Optimization

For each approved optimization:
1. Show the before/after diff
2. Estimate token savings
3. Apply the change after approval

Track cumulative savings as changes are applied.

## Rules

1. NEVER remove information that is genuinely useful - compress, don't delete
2. Show diffs before every change
3. Preserve all project-specific gotchas and non-obvious patterns
4. Focus on removing filler, not substance
