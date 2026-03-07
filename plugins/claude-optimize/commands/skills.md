---
description: Skill lifecycle - inventory, trigger quality, gaps
argument-hint: "[focus-area]"
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(wc:*)
  - Bash(head:*)
  - Bash(python3:*)
  - AskUserQuestion
---

# Optimize: Skills

Arguments: `$ARGUMENTS`

You are the Claude Optimize skill analyzer. Assess the skill ecosystem in this Claude Code environment.

## Workflow

### Phase 1: Inventory Skills

Discover all skills from:
- `.claude/skills/*/SKILL.md` (project skills)
- `~/.claude/skills/*/SKILL.md` (personal skills)
- Plugin skills (from installed plugins)

For each skill, extract:
- Name, description, version
- Description word count
- Allowed tools
- Whether it's user-invocable or auto-triggering

### Phase 2: Trigger Quality Assessment

For each skill description, evaluate:

| Quality | Criteria |
|---------|----------|
| Excellent | Specific trigger conditions, includes "when" and "do not trigger" |
| Good | Clear purpose, reasonable trigger scope |
| Fair | Vague, could trigger on unrelated tasks |
| Poor | Too broad or too narrow, will mis-trigger |

**Key insight**: Claude tends to "undertrigger" skills — not using them when they'd be useful. Descriptions should be slightly "pushy" and list concrete trigger phrases/contexts, not just state what the skill does.

Flag:
- Descriptions > 150 words (bloated, wastes context)
- Descriptions < 20 words (too vague for reliable triggering)
- Descriptions without "do not trigger" clauses (risk of false positives)
- Descriptions that only say what the skill does, not when to use it
- Overlapping triggers between skills

### Phase 3: Gap Analysis

If session logs are available, use the **session-analyzer** skill to identify:
- Repeated workflows that no skill covers
- Frequently used tool patterns without skill wrappers
- Commands run manually that could be skills

Check memory files for:
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
