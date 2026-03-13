---
description: Skill lifecycle - inventory, trigger quality, gaps
argument-hint: "[focus-area]"
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(python3:*)
  - AskUserQuestion
---

# Optimize: Skills

Arguments: `$ARGUMENTS`

You are the Claude Optimize skill analyzer. Assess the skill ecosystem in this Claude Code environment.

## Workflow

### Phase 1: Inventory and Assess Skills

ALWAYS use the bundled script for skill inventory and trigger quality assessment. Do NOT manually glob for skills, count words, assess trigger quality, or pipe script output through Python, append `2>&1` or other shell redirects. Scripts have a `--summary` flag if you need only aggregate numbers.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skill_analyzer.py --auto-discover --json
```

The script automatically:
- Discovers all skills from project, personal, and plugin directories
- Extracts name, description, word count from YAML frontmatter
- Assesses trigger quality (excellent/good/fair/poor) based on:
  - Word count thresholds (flag >150 words bloated, <20 words vague)
  - Presence of "do not trigger" clauses
  - Presence of explicit trigger conditions
- Detects overlapping descriptions via Jaccard similarity (>70% threshold)

### Phase 2: Review Results

**Key insight**: Claude tends to "undertrigger" skills — not using them when they'd be useful. Descriptions should be slightly "pushy" and list concrete trigger phrases/contexts, not just state what the skill does.

### Phase 3: Gap Analysis

If session logs are available, use the **session-analyzer** skill to identify:
- Repeated workflows that no skill covers
- Frequently used tool patterns without skill wrappers
- Commands run manually that could be skills

If memory files exist (check via `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/env_inventory.py --component memory --json --summary`), Read those files and look for:
- Documented patterns that should be skills
- Repeated instructions that indicate missing skills

### Phase 4: Generate Report

```markdown
## Skill Analysis Report

### Inventory ([count] skills)
| Skill | Source | Description Words | Trigger Quality |
|-------|--------|-------------------|-----------------|
| [name] | project/plugin | XX | [rating] |

### Trigger Issues
| Skill | Issue | Suggested Fix |
|-------|-------|---------------|
| [name] | [issue] | [fix] |

### Overlapping Triggers
| Skill A | Skill B | Overlap Area |
|---------|---------|-------------|
| [name] | [name] | [description] |

### Gaps (Skills to Create)
| Opportunity | Evidence | Priority |
|-------------|----------|----------|
| [workflow] | [session/memory evidence] | [level] |

### Recommendations
1. [specific action]
```

## Rules

1. Read-only analysis - do not create or modify skills
2. Cite specific evidence for gap recommendations
3. Focus on trigger quality over skill count
4. For skills needing improvement, recommend the skill-creator plugin if installed
