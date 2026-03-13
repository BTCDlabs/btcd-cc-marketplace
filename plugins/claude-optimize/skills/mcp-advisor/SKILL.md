---
name: mcp-advisor
description: >
  Use when running /optimize:mcp to analyze MCP server configuration, recommend new
  servers based on detected project stack, perform health checks, and assess security.
  Triggers on MCP server optimization, MCP recommendations, or MCP health checking.
  Do NOT trigger on MCP server development or general coding tasks.
---

# MCP Advisor

Analyzes MCP server configuration and recommends improvements based on project stack. Powers `/optimize:mcp` and the MCP configuration dimension of `/optimize:audit`.

## Analysis Workflow

### Step 1: Read Current MCP Configuration

Read `.mcp.json` at project root and `~/.claude/settings.json` for global MCP config.

For each server, record:
- Name
- Command and args
- Environment variables
- Transport type (stdio, HTTP, SSE)

### Step 2: Health Check

ALWAYS use the bundled script for MCP health checks. Do NOT manually run `which`, `command -v`, or check env vars.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/mcp_health_check.py --json
```

The script checks each configured server for:
1. **Existence check**: Command exists on system (via `which`)
2. **Dependency check**: Required packages are reachable
3. **Configuration check**: Required env vars are set

### Step 3: Stack-Based Recommendations

Cross-reference detected project stack (from codebase-analyzer) with MCP server catalog.

Reference: `${CLAUDE_PLUGIN_ROOT}/skills/mcp-advisor/references/mcp-catalog.md`

### Step 4: Context Impact Assessment

The MCP health check script (Step 2) includes token impact estimates. It uses a built-in catalog of known MCP servers to estimate tool counts and calculates:
- ~150 tokens per always-loaded tool
- ~20 tokens per deferred tool

### Step 5: Security Assessment

Delegate to security-auditor skill's MCP security checks, or inline:
- Check `enableAllProjectMcpServers`
- Verify credential handling
- Assess trust level

### Step 6: Generate Report

```markdown
## MCP Configuration Report

**Overall Grade**: [A-F] ([score]/100)

### Configured Servers ([count])
| Server | Status | Tools (est.) | Security | Impact |
|--------|--------|-------------|----------|--------|
| [name] | Healthy/Error | XX | OK/Warning | ~XXX tokens |

### Health Issues
| Server | Issue | Fix |
|--------|-------|-----|
| [name] | [description] | [action] |

### Recommended Servers (based on stack)
| Server | Why | Install |
|--------|-----|---------|
| [name] | [detected stack reason] | [install command] |

### Context Impact
- Total always-loaded tools: [count] (~XXX tokens)
- Recommended: Move [count] tools to deferred loading

### Security Summary
[From security-auditor MCP checks]
```

## Scoring Contribution

MCP configuration dimension (10% of total score):
- Server health: 30 points
- Stack relevance: 25 points
- Security posture: 25 points
- Context efficiency: 20 points
