---
name: context-optimizer
description: >
  Use when running /optimize:context to analyze and reduce token consumption in Claude Code
  configuration. Measures CLAUDE.md token count, skill description bloat, MCP tool count,
  and recommends compaction strategies. Triggers on context optimization, token reduction,
  or CLAUDE.md bloat analysis. Do NOT trigger on general coding tasks.
---

# Context Optimizer

Analyzes Claude Code environment for token efficiency and recommends reductions. Powers `/optimize:context` and the context efficiency dimension of `/optimize:audit`.

## Why Context Matters

Claude Code reserves a buffer of ~33K-45K tokens for system instructions, CLAUDE.md content, skill descriptions, and tool definitions. Every token used by configuration is a token unavailable for actual work. Bloated configurations lead to:
- Earlier compaction events (losing conversation context)
- Slower response times
- Less room for complex reasoning

## Analysis Workflow

### Step 1: Measure CLAUDE.md Token Load

Read all CLAUDE.md variants and estimate token count:
- `CLAUDE.md` (project root)
- `.claude.md`, `.claude.local.md`
- Nested `CLAUDE.md` files in subdirectories (discovered via Glob)

**Token estimation**: Count characters, divide by 4 (rough approximation). For precise count, count words and multiply by 1.3.

**Targets**:
- Excellent: <1000 tokens (<200 lines)
- Good: 1000-2000 tokens (200-400 lines)
- Warning: 2000-3000 tokens (400-600 lines)
- Critical: >3000 tokens (>600 lines)

### Step 2: Analyze Instruction Density

For each CLAUDE.md file, evaluate:

#### Redundancy Detection
- Instructions that repeat the same thing in different words
- Instructions that duplicate Claude's default behavior (e.g., "write clean code")
- Instructions copied from templates that don't apply to this project

#### Verbosity Detection
- Instructions that use 3 sentences where 1 would suffice
- Excessive examples where 1 example demonstrates the pattern
- Long explanations for simple conventions

#### Staleness Detection
- References to files/patterns that no longer exist
- Instructions for tools/frameworks no longer in use
- Outdated version numbers or API references

### Step 3: Analyze Skill Description Sizes

Read all SKILL.md files (project + plugins). For each:
- Measure description field length (from YAML frontmatter)
- Descriptions are loaded into context for trigger matching
- Target: <100 words per description

Flag descriptions that are:
- Over 150 words (bloated)
- Under 20 words (too vague for good triggering)
- Contain implementation details (should be in body, not description)

### Step 4: Analyze MCP Tool Count

Read `.mcp.json` and check:
- Total number of MCP servers configured
- Whether Tool Search / deferred loading is being used
- Estimate tool count per server (if known servers)

Each always-loaded MCP tool adds ~100-200 tokens to context. Deferred tools add ~20 tokens (just the search entry).

### Step 5: Check Compaction Resilience

Look for PreCompact hook:
- Does a PreCompact hook exist?
- Does it preserve critical context during compaction?
- Does it save important state that would otherwise be lost?

If no PreCompact hook exists, recommend creating one that preserves:
- Current task/goal
- Key file paths being worked on
- Important decisions made
- Uncommitted changes summary

### Step 6: Generate Report

```markdown
## Context Efficiency Report

**Overall Grade**: [A-F] ([score]/100)

### CLAUDE.md Token Budget ([score]/40)
| File | Lines | Est. Tokens | Status |
|------|-------|-------------|--------|
| CLAUDE.md | XX | ~XXXX | [grade] |
| .claude.local.md | XX | ~XXXX | [grade] |
| Total | XX | ~XXXX | [grade] |

### Instruction Quality ([score]/25)
| Issue | Count | Impact |
|-------|-------|--------|
| Redundant instructions | X | ~XXX tokens recoverable |
| Verbose instructions | X | ~XXX tokens recoverable |
| Stale instructions | X | ~XXX tokens recoverable |
| Default-behavior duplicates | X | ~XXX tokens recoverable |

### Skill Description Efficiency ([score]/20)
| Skill | Description Words | Status |
|-------|-------------------|--------|
| [name] | XX | [OK/Bloated/Vague] |

### MCP Tool Load ([score]/15)
| Server | Tools (est.) | Loading | Impact |
|--------|--------------|---------|--------|
| [name] | XX | Always/Deferred | ~XXX tokens |

### Compaction Resilience
- PreCompact hook: Present/Missing
- Critical context preservation: Yes/No

### Recommended Actions
1. [Action] - saves ~XXX tokens
2. [Action] - saves ~XXX tokens
Total recoverable: ~XXXX tokens
```

## Compression Techniques

Reference: `${CLAUDE_PLUGIN_ROOT}/skills/context-optimizer/references/compaction-strategies.md`

### Quick Wins
- Remove comments and explanations that duplicate obvious code conventions
- Replace verbose examples with concise one-liners
- Remove instructions for tools/frameworks not in the project
- Deduplicate instructions across CLAUDE.md files

### Structural Improvements
- Use bullet points instead of paragraphs
- Use tables for structured rules
- Move detailed references to memory files (loaded on demand, not always)
- Use hierarchical CLAUDE.md (root has essentials, subdirectories have specifics)

## Scoring Contribution

Context efficiency dimension (15% of total score):
- CLAUDE.md token budget: 40 points
- Instruction quality: 25 points
- Skill description efficiency: 20 points
- MCP tool load: 15 points
