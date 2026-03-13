---
name: claude-md-manager
description: >
  Use when running /optimize:init, /optimize:audit, or /optimize:context to assess
  CLAUDE.md quality, generate templates, and suggest improvements. Scores files using
  a weighted rubric covering commands, architecture, patterns, conciseness, currency,
  and actionability. Do NOT trigger on general file editing or coding tasks.
---

# CLAUDE.md Manager

Assesses and improves CLAUDE.md files using a structured quality rubric. Powers the CLAUDE.md quality dimension across `/optimize:init`, `/optimize:audit`, and `/optimize:context`.

## Assessment Workflow

### Step 1: Discover, Score, and Cross-Reference

ALWAYS use the bundled scripts. Do NOT use Glob to discover CLAUDE.md files, manually count tokens, parse package.json, or run any ad-hoc shell commands.

```bash
# Discover all CLAUDE.md files and measure token load
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/token_counter.py --claude-md --json --summary

# Score quality, validate commands, and check file path references
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/claude_md_validator.py --auto-discover --json
```

The token_counter recursively finds all CLAUDE.md variants (project root, subdirectories, `.claude.local.md`, `~/.claude/`) and reports token counts with bands.

The validator automatically:
- Extracts commands from code blocks and inline backticks
- Validates commands against `package.json` scripts and `Makefile` targets
- Checks if all referenced file paths exist
- Scores each CLAUDE.md on the 6-dimension rubric
- Reports invalid commands and missing paths

### Step 2: Interpret Scores

The validator scores on 6 dimensions (total 100):

| Dimension | Points | Key Question |
|-----------|--------|--------------|
| Commands/Workflows | 20 | Are build/test/lint/deploy commands documented? |
| Architecture Clarity | 20 | Can Claude understand where things live? |
| Non-Obvious Patterns | 15 | Are gotchas, quirks, and workarounds captured? |
| Conciseness | 15 | Is every line earning its place? No filler? |
| Currency | 15 | Does it reflect the actual current codebase? |
| Actionability | 15 | Can instructions be copy-pasted and executed? |

**Grade Scale**: A (90-100), B (70-89), C (50-69), D (30-49), F (0-29)

Quality rubric reference: `${CLAUDE_PLUGIN_ROOT}/skills/claude-md-manager/references/quality-criteria.md`

### Step 3: Identify Improvements

For each issue found, categorize:
- **Missing content**: Key section absent (use templates reference)
- **Stale content**: References to things that no longer exist
- **Verbose content**: Could be compressed without losing information
- **Redundant content**: Duplicates Claude's default behavior
- **Inaccurate content**: Contradicts actual codebase state

### Step 4: Generate Assessment

```markdown
## CLAUDE.md Quality Assessment

### File: [path]
**Grade**: [A-F] ([score]/100)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Commands/Workflows | XX/20 | [brief note] |
| Architecture Clarity | XX/20 | [brief note] |
| Non-Obvious Patterns | XX/15 | [brief note] |
| Conciseness | XX/15 | [brief note] |
| Currency | XX/15 | [brief note] |
| Actionability | XX/15 | [brief note] |

### Red Flags
- [specific issue with line reference]

### Suggested Improvements
1. [specific improvement with diff preview]
2. [specific improvement with diff preview]
```

## For /optimize:init (New File Generation)

When no CLAUDE.md exists, generate one using:
`${CLAUDE_PLUGIN_ROOT}/skills/claude-md-manager/references/templates.md`

1. Use codebase-analyzer results to detect project type
2. Select appropriate template (minimal, comprehensive, monorepo)
3. Fill in detected values (commands from package.json, architecture from directory structure)
4. Present the generated file for user approval before writing

## Update Guidelines

Follow the principles in:
`${CLAUDE_PLUGIN_ROOT}/skills/claude-md-manager/references/update-guidelines.md`

Key rules:
- Only add project-specific information
- No generic best practices
- One line per concept when possible
- Commands must be copy-paste ready
- Verify all file paths exist
- Show diff before applying changes

## Common Issues to Flag

- **Stale commands**: Build/test commands that no longer work
- **Missing dependencies**: Setup steps that skip required installs
- **Outdated architecture**: Descriptions referencing deleted files/folders
- **Missing environment setup**: No mention of required env vars or config
- **Broken test commands**: Test invocations with wrong paths or flags
- **Undocumented gotchas**: Known issues that waste time when not captured

## User Tips to Share

- Use `#` in Claude Code to quickly add info to CLAUDE.md from conversation
- Keep it concise — every line should save Claude time or prevent mistakes
- Make commands copy-paste ready (no placeholder values without explanation)
- Use `.claude.local.md` for personal preferences, `CLAUDE.md` for team conventions
- Put user-wide preferences in `~/.claude/CLAUDE.md` for global defaults

## What Makes a Great CLAUDE.md

**Key principles**: Project-specific, concise, actionable, current.

**Recommended sections**: Commands, Architecture, Key Files, Code Style, Environment, Testing, Gotchas, Workflow.

Avoid: generic advice, restating obvious code, documenting what Claude already knows, TODO items that never get completed.

## Scoring Contribution

CLAUDE.md quality dimension (20% of total score):
- Direct rubric score from assessment (0-100)
- Applied across all CLAUDE.md files (weighted by relevance)
