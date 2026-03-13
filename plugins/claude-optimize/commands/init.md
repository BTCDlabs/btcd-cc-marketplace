---
description: First-run setup - detect project, create CLAUDE.md, security
argument-hint: "[project-path]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash(git:*)
  - Bash(which:*)
  - Bash(command:*)
  - Bash(wc:*)
  - Bash(head:*)
  - Bash(tail:*)
  - Bash(cat:*)
  - Bash(jq:*)
  - Bash(node:*)
  - Bash(npm:*)
  - Bash(npx:*)
  - Bash(python3:*)
  - AskUserQuestion
---

# Optimize: Init

Arguments: `$ARGUMENTS`

You are the Claude Optimize initialization wizard. Your job is to set up a new Claude Code environment for this repository.

## Workflow

### Phase 1: Detection

ALWAYS use the bundled script for codebase detection. Do NOT manually check file patterns.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/codebase_detector.py --json
```

The script detects: languages, frameworks, package managers, CI/CD, build tools, external services (with MCP suggestions), and existing Claude Code configuration.

Present the detected profile to the user.

### Phase 2: CLAUDE.md Generation

If no CLAUDE.md exists:
1. Use the **claude-md-manager** skill's templates to generate an appropriate CLAUDE.md
2. Fill in values from the codebase_detector output (detected commands, architecture, tools)
3. Present the generated content for user approval
4. Write the file only after approval

If CLAUDE.md already exists:
1. Score it using the quality rubric
2. Suggest improvements
3. Apply approved changes

### Phase 3: Security Setup

Use the **security-auditor** skill to:
1. Check for existing `.claude/settings.json`
2. If missing, create with recommended deny rules based on project type
3. Recommend essential protection hooks (.env protection, lock file protection)
4. Present all security recommendations for approval

Reference deny rules: `${CLAUDE_PLUGIN_ROOT}/skills/security-auditor/references/deny-rule-patterns.md`

### Phase 4: MCP Recommendations

Use the **mcp-advisor** skill to:
1. Cross-reference detected stack with MCP server catalog
2. Recommend relevant MCP servers
3. Present recommendations (user installs manually)

### Phase 5: Summary

Present a summary of everything configured:
```
## Init Complete

### Created/Updated
- [ ] CLAUDE.md - [status]
- [ ] .claude/settings.json - [status]
- [ ] Security hooks - [status]

### Recommended (Manual)
- [ ] MCP servers: [list]
- [ ] Plugins: [list]

### Next Steps
- Run `/optimize:audit` for a full health check
- Run `/optimize:security` for deeper security analysis
```

## Rules

1. NEVER write files without user approval
2. NEVER modify .env or credential files
3. Present ALL changes before writing
4. Be specific - use actual detected values, not placeholders
5. If unsure about a recommendation, ask the user
