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

#### Deny Rules Assessment
Check `.claude/settings.json` for `deny` array. Score based on presence of recommended deny rules.

Reference: `${CLAUDE_PLUGIN_ROOT}/skills/security-auditor/references/deny-rule-patterns.md`

Essential deny rules that should exist:
- `rm -rf /` and variants
- `chmod 777`
- Commands that read/write `.env`, `.key`, credential files
- `curl | bash` and `wget | sh` pipe-to-shell patterns
- `git push --force` to main/master
- `DROP TABLE`, `DELETE FROM` without WHERE

#### Allow Rules Assessment
Check `allow` array for overly broad patterns:
- **Critical**: `Bash(*)` allows ALL bash commands - extremely dangerous
- **Warning**: `Bash(rm:*)` allows all rm variants
- **Warning**: `Bash(curl:*)` without restrictions
- **OK**: `Bash(git:*)` - scoped to git commands
- **OK**: `Bash(npm:*)` - scoped to npm

### Step 3: MCP Server Security

For each MCP server in `.mcp.json`:

1. **Transport security**: Is it using HTTPS? (for HTTP-based servers)
2. **Authentication**: Does it require API keys or tokens?
3. **Trust level**: Is it from a known/trusted source?
4. **Scope**: What tools does it expose? Are they overly broad?
5. **Environment variables**: Are secrets properly externalized?

Check `enableAllProjectMcpServers` - if `true`, flag as critical risk.

Reference: `${CLAUDE_PLUGIN_ROOT}/skills/security-auditor/references/mcp-security-checklist.md`

### Step 4: Hook Security

For each hook script:
1. Does it properly validate input?
2. Does it use `set -euo pipefail`?
3. Does it have injection vulnerabilities (unquoted variables in commands)?
4. Does it write to sensitive locations?
5. Does it have appropriate timeouts?

### Step 5: .env Protection

Check if there are hooks preventing writes to sensitive files:
- `.env`, `.env.*`
- `*.key`, `*.pem`, `*.cert`
- `credentials.*`, `secrets.*`
- `~/.ssh/*`

If no protection hooks exist, recommend creating one.

### Step 6: Skill/Agent Prompt Injection Scan

For each skill and agent markdown file:
- Check for instructions that could bypass safety (e.g., "ignore previous instructions")
- Check for instructions that access credential files
- Check for overly broad tool permissions
- Check for instructions that disable hooks or verification

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
