---
name: memory-manager
description: >
  Use when running /optimize:memory to analyze memory file hygiene, detect stale entries,
  find duplicates, identify migration candidates to CLAUDE.md, and suggest reorganization.
  Triggers on memory optimization, memory cleanup, or memory hygiene analysis.
  Do NOT trigger on general coding tasks or file editing.
---

# Memory Manager

Analyzes Claude Code memory files for hygiene, staleness, duplicates, and migration opportunities. Powers the `/optimize:memory` mode.

## Analysis Workflow

### Step 1: Discover and Analyze Memory Files

ALWAYS use the bundled scripts. Do NOT use Glob to find memory directories, manually read `~/.claude/projects/`, count lines, estimate tokens, or run any ad-hoc shell commands.

```bash
# Discover and inventory all memory files with token counts
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/env_inventory.py --component memory --json

# Detect stale entries and find duplicates
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/memory_staleness.py --check-duplicates --json
```

The env_inventory automatically discovers the project's memory directory under `~/.claude/projects/`, finds all `.md` files including `MEMORY.md`, and reports token counts.

The staleness script automatically:
- Extracts file paths, function names, and package names from each entry
- Searches the codebase to verify references still exist
- Calculates staleness scores (0-25)
- Detects exact and near-duplicate entries via Jaccard similarity

### Step 3: Score Each Entry

Score entries on four dimensions (each 0-25, total 0-100):

#### Staleness (0-25)
- 25: References current patterns confirmed in codebase
- 15: References patterns that likely still apply
- 5: References patterns with no evidence of current relevance
- 0: References removed/renamed files, deprecated APIs, or old patterns

The staleness script (Step 2) provides automated staleness scores. For accuracy, relevance, and actionability, use the scoring rubric below.

#### Accuracy (0-25)
- 25: Statement is verifiably correct by reading referenced code
- 15: Statement is plausible but not easily verified
- 5: Statement is vague or overly general
- 0: Statement contradicts current codebase state

#### Relevance (0-25)
- 25: Directly affects daily development workflow
- 15: Useful context but not frequently needed
- 5: Nice-to-know but rarely actionable
- 0: No longer relevant to current project state

#### Actionability (0-25)
- 25: Clear instruction that changes behavior (e.g., "always use bun, not npm")
- 15: Helpful pattern but not prescriptive (e.g., "the auth system uses JWT")
- 5: Pure documentation with no behavioral implication
- 0: Empty or redundant statement

### Step 4: Identify Migration Candidates

Entries should migrate to CLAUDE.md if they meet ALL of:
- Score >= 70 (high quality)
- Team-wide relevance (not personal preference)
- Prescriptive (tells Claude what to do, not just context)
- Not already in CLAUDE.md

Entries should become skills if they:
- Describe a multi-step workflow
- Are referenced frequently across sessions
- Include specific tool usage patterns

### Step 5: Identify Duplicates

Compare entries across all memory files for:
- **Exact duplicates**: Same content in different files
- **Semantic duplicates**: Different wording, same meaning
- **Contradictions**: Entries that say opposite things

### Step 6: Generate Report

```markdown
## Memory Health Report

**Files analyzed**: [count]
**Total entries**: [count]
**Total tokens**: [estimate]
**MEMORY.md status**: [lines]/200 line limit

### Scoring Summary

| File | Entries | Avg Score | Stale | Duplicates |
|------|---------|-----------|-------|------------|
| MEMORY.md | N | XX | N | N |
| file2.md | N | XX | N | N |

### Stale Entries (recommend removal)
[List entries with staleness score < 10]

### Migration Candidates (recommend move to CLAUDE.md)
[List entries meeting migration criteria]

### Skill Candidates (recommend creating skills)
[List entries describing repeatable workflows]

### Duplicates Found
[List duplicate pairs with file locations]

### Contradictions Found
[List contradicting entries]

### Recommended Actions
1. [Specific action with file path]
2. [Specific action with file path]
...
```

### Step 7: Present and Await Approval

Present the report and ask:
**"Which actions would you like me to take? (e.g., 1,3,5 or all or none)"**

NEVER modify memory files without explicit user approval.

## Scoring Contribution

Memory hygiene dimension (10% of total):
- Average entry score across all files
- Penalize: >200 lines in MEMORY.md (-10), duplicates (-5 each), contradictions (-10 each)
- Bonus: Well-organized semantic grouping (+5), links from MEMORY.md to topic files (+5)
