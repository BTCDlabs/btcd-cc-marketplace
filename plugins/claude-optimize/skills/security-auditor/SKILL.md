---
name: security-auditor
description: >
  Use when running /optimize:security or /optimize:init to audit Claude Code security
  posture including permissions, deny rules, MCP server trust, hook safety, and prompt
  injection vectors. Triggers on security hardening, permission auditing, or deny rule
  analysis for Claude Code. Do NOT trigger on application security reviews or general coding.
---

# Security Auditor

Analyzes Claude Code environment security posture and recommends hardening measures. Powers `/optimize:security` and the security dimension of `/optimize:audit`.

## Analysis Workflow

### Step 1: Read Current Security Configuration

Read these files (all in parallel):
- `.claude/settings.json` - permissions (allow/deny rules)
- `.claude/settings.local.json` - personal overrides
- `.mcp.json` - MCP server configuration
- `CLAUDE.md` - check for security-related instructions
- `.claude/skills/*/SKILL.md` - scan skill allowed-tools
- Glob `hooks/` directories for hook scripts

### Step 2: Permission Analysis

ALWAYS use the bundled script for permission auditing. Do NOT manually parse settings.json or check deny/allow rules.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/permission_auditor.py --json
```

The script automatically:
- Checks for all critical and high-priority deny rules from the deny-rule-patterns reference
- Flags overly broad allow patterns (Bash(*), Bash(rm:*), Bash(sudo:*), etc.)
- Checks for sensitive file protection
- Calculates a security score (0-100) with grade

Reference: `${CLAUDE_PLUGIN_ROOT}/skills/security-auditor/references/deny-rule-patterns.md`

### Step 3: MCP Server Security

ALWAYS use the bundled script for MCP security analysis. Do NOT manually parse .mcp.json or check trust settings.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/mcp_health_check.py --json
```

The script automatically checks: command existence, environment variables, tool count estimation, token impact, AND `enableAllProjectMcpServers` trust setting in settings.json (flagged as critical if true).

Reference: `${CLAUDE_PLUGIN_ROOT}/skills/security-auditor/references/mcp-security-checklist.md`

### Step 4: Hook Security

ALWAYS use the bundled script for hook security validation. Do NOT manually inspect scripts.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/hook_validator.py --settings .claude/settings.json --json
```

The script checks for: input validation, `set -euo pipefail`, injection vulnerabilities, missing permissions, syntax errors, and file reference validity.

### Step 5: .env Protection

The permission auditor script (Step 2) automatically checks for .env protection hooks. Review the `env_protection` field in the output. If `has_protection` is false, recommend creating a PreToolUse hook for Write/Edit that blocks writes to sensitive files (.env, *.key, *.pem, *.cert, credentials.*, secrets.*).

### Step 6: Skill/Agent Prompt Injection Scan

ALWAYS use the bundled script for prompt injection scanning. Do NOT manually read and scan skill/agent files.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/prompt_injection_scanner.py --auto-discover --json
```

The script automatically scans all SKILL.md and agent .md files for: safety bypass instructions, credential access patterns, overly broad tool permissions, and hook/verification disable patterns.

### Step 7: Generate Security Scorecard

```markdown
## Security Scorecard

**Overall Grade**: [A-F] ([score]/100)

### Permission Security ([score]/30)
| Check | Status | Risk |
|-------|--------|------|
| Deny rules present | Yes/No | [level] |
| Essential denys covered | X/Y | [level] |
| Overly broad allows | [count] | [level] |
| Bash(*) present | Yes/No | Critical/OK |

### MCP Security ([score]/25)
| Server | Transport | Auth | Trust | Risk |
|--------|-----------|------|-------|------|
| [name] | HTTPS/HTTP | Yes/No | High/Med/Low | [level] |

| Check | Status |
|-------|--------|
| enableAllProjectMcpServers | true/false |
| Untrusted servers | [count] |

### Hook Security ([score]/20)
| Check | Status |
|-------|--------|
| .env protection | Present/Missing |
| Hook input validation | [count]/[total] |
| Injection risks | [count] |

### Skill/Agent Security ([score]/15)
| Check | Status |
|-------|--------|
| Skills scanned | [count] |
| Injection vectors found | [count] |
| Overly broad permissions | [count] |

### Configuration Security ([score]/10)
| Check | Status |
|-------|--------|
| settings.json exists | Yes/No |
| Local overrides exist | Yes/No |
| CLAUDE.md security instructions | Present/Missing |

### Recommended Actions
1. [Critical] [specific action]
2. [Warning] [specific action]
3. [Info] [specific action]
```

## Scoring Contribution

Security posture dimension (20% of total score):
- Permission security: 30 points
- MCP security: 25 points
- Hook security: 20 points
- Skill/agent security: 15 points
- Configuration security: 10 points
