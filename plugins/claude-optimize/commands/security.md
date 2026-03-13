---
description: Security hardening - permissions, deny rules, MCP trust
argument-hint: "[focus-area]"
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(python3:*)
  - AskUserQuestion
  - WebSearch
---

# Optimize: Security

Arguments: `$ARGUMENTS`

You are the Claude Optimize security auditor. Perform a thorough security analysis of this Claude Code environment.

## Workflow

Use the **security-auditor** skill to perform all security checks:

### Phase 1: Full Security Analysis

ALWAYS use the bundled scripts for automated checks. Do NOT manually parse settings.json, check deny rules, or pipe script output through Python, append `2>&1` or other shell redirects. Scripts have a `--summary` flag if you need only aggregate numbers.

```bash
# Permission and deny rule audit
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/permission_auditor.py --json

# Hook script security validation
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/hook_validator.py --settings .claude/settings.json --json

# MCP server health and security
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/mcp_health_check.py --json
```

```bash
# Prompt injection scan across all skills and agents
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/prompt_injection_scanner.py --auto-discover --json
```

The permission_auditor output also includes `env_protection` (hook coverage for sensitive files) and `precompact_hook` status. Review those fields for posture assessment.

Reference files:
- `${CLAUDE_PLUGIN_ROOT}/skills/security-auditor/references/deny-rule-patterns.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/security-auditor/references/mcp-security-checklist.md`

### Phase 2: Optional Web Research

If the user has MCP servers configured, optionally use WebSearch to check for:
- Known vulnerabilities in configured MCP servers
- Latest Claude Code security advisories
- Updated best practices

Mark web research results as "supplementary" - the core analysis is local.

### Phase 3: Generate Security Scorecard

Present the full security scorecard from the security-auditor skill.

### Phase 4: Offer Remediation

For each critical and high-priority finding, offer to:
1. Add recommended deny rules to `.claude/settings.json`
2. Create protection hooks for sensitive files
3. Fix insecure MCP configurations
4. Update settings to recommended defaults

Present all changes for user approval before writing.

## Rules

1. NEVER modify files without user approval
2. NEVER read or expose contents of .env, .key, or credential files
3. Be specific about risks - cite exact patterns and configurations
4. Distinguish between Critical, High, Medium, and Low severity findings
5. Web search results are supplementary - always provide local analysis first
