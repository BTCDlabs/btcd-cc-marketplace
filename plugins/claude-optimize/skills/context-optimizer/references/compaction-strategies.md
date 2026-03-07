# Compaction Strategies

Techniques for reducing token consumption in Claude Code configuration.

## CLAUDE.md Compression

### Before (Verbose - ~150 tokens)
```
When you are writing TypeScript code, please make sure to always use strict mode.
This means you should have "strict": true in your tsconfig.json file. Also, please
make sure to use proper type annotations on all function parameters and return types.
Do not use the 'any' type unless absolutely necessary, and if you do use it, please
add a comment explaining why.
```

### After (Concise - ~40 tokens)
```
TypeScript: strict mode, explicit types on all functions, no `any` without justification comment.
```

### Reduction: 73%

## Common Bloat Patterns

### 1. Default Behavior Duplication
Remove instructions that tell Claude to do what it already does:
- "Write clean, readable code" (default behavior)
- "Follow best practices" (too vague, and default)
- "Add error handling" (Claude does this by default)
- "Use meaningful variable names" (default behavior)

### 2. Over-Specified Tool Usage
Remove unless project has non-standard needs:
- "Use Read to read files" (Claude knows this)
- "Use Edit instead of sed" (system instructions already say this)
- "Use Glob to find files" (system instructions already say this)

### 3. Excessive Examples
One example is usually sufficient:
- Before: 5 examples of commit message format -> After: 1 example + the rule
- Before: 3 examples of test naming -> After: pattern description + 1 example

### 4. Paragraph Instructions
Convert paragraphs to bullet points:
- Saves ~30% tokens on average
- Faster for Claude to parse
- Easier to maintain

## Structural Strategies

### Hierarchical CLAUDE.md
```
CLAUDE.md (root)          # Universal rules only (~500 tokens)
packages/api/CLAUDE.md    # API-specific rules (~300 tokens)
packages/web/CLAUDE.md    # Web-specific rules (~300 tokens)
```
Only the relevant file loads based on working directory context.

### Memory File Offloading
Move reference data to memory files:
- Architecture decisions -> memory/architecture.md
- Debugging notes -> memory/debugging.md
- API patterns -> memory/patterns.md

Memory files load on demand, not always. CLAUDE.md loads always.

### Skill Consolidation
If you have 5 skills with 100-word descriptions each = 500 words always in context.
Consider:
- Merging related skills (3 testing skills -> 1 testing skill)
- Shortening descriptions to <50 words each
- Moving details from description to SKILL.md body

## PreCompact Hook Template

```bash
#!/bin/bash
# PreCompact hook - preserve critical context during compaction
cat <<'EOF'
## Preserved Context
Key files: [auto-populated from recent tool calls]
Current task: [from conversation context]
Decisions made: [from conversation context]
EOF
```

This ensures critical information survives context compaction events.

## Token Budget Guidelines

| Component | Recommended Max | Notes |
|-----------|----------------|-------|
| CLAUDE.md (all files) | 2000 tokens | ~400 lines total |
| Each skill description | 50-100 words | In YAML frontmatter |
| MCP tools (always loaded) | 10 tools | Use deferred for rest |
| Hook definitions | N/A | Minimal token impact |
| Agent definitions | N/A | Only loaded when selected |

**Total budget**: ~5000-8000 tokens for all configuration. Leave 25K+ for actual conversation.
