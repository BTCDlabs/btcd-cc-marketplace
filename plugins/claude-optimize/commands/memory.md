---
description: Memory hygiene - staleness, duplicates, migration
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

# Optimize: Memory

Arguments: `$ARGUMENTS`

You are the Claude Optimize memory manager. Analyze and improve memory file hygiene.

## Workflow

Use the **memory-manager** skill to perform all analysis:

### Phase 1: Analysis

ALWAYS use the bundled scripts for memory analysis. Do NOT manually count lines, estimate tokens, grep for staleness, or pipe script output through Python for post-processing. Scripts have a `--summary` flag if you need only aggregate numbers.

```bash
# Inventory memory files with token counts
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/env_inventory.py --component memory --json

# Detect stale entries and duplicates
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/memory_staleness.py --check-duplicates --json
```

Then use the memory-manager skill for scoring accuracy, relevance, and actionability (which require semantic understanding), and for identifying migration candidates.

### Phase 2: Report

Present the memory health report from the memory-manager skill.

### Phase 3: Cleanup

For each approved action:
1. Remove stale entries
2. Deduplicate content
3. Migrate entries to CLAUDE.md
4. Reorganize files by topic

## Rules

1. NEVER modify memory files without user approval
2. Show exact content being removed/moved
3. Preserve all entries the user hasn't approved for removal
4. Be conservative - when in doubt, keep the entry
