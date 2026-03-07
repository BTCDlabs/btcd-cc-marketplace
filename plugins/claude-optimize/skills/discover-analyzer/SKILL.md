---
name: discover-analyzer
description: >
  Use when running /optimize:discover to cross-reference session usage data against
  the current environment inventory. Detects gaps (repeated manual work that could be
  automated), bloat (unused skills, MCP servers, agents), and calculates tooling balance.
  Do NOT trigger on general coding tasks or other optimize modes.
---

# Discover Analyzer

Cross-references session usage data against the current environment inventory to find gaps (things to add) and bloat (things to remove). This is the analytical core of `/optimize:discover`.

## Inputs

You receive three data sets from the discover command's parallel agents:

1. **Session Analysis** — tool usage counts, bash command patterns, file edit frequency, errors, workflow sequences, branch names
2. **Environment Inventory** — all skills, agents, hooks, MCP servers with descriptions and sources
3. **Codebase Profile** — project type, language, framework, package manager, CI/CD

## Gap Detection

Gaps are things the user does manually that could be automated. Cross-reference session data against the inventory:

### Bash Command Gaps

For each bash command pattern appearing 5+ times across sessions:
1. Check if any existing skill covers this workflow
2. Check if any existing hook automates this
3. If neither → gap candidate for a new skill or hook

**Examples:**
- `npm test` run 47 times → candidate for a test-runner hook or skill
- `prettier --write` run 23 times → candidate for a format-on-save hook
- `docker compose up` run 15 times → candidate for a dev-environment skill

### Workflow Sequence Gaps

Look for ordered tool-call patterns that repeat across sessions:
- `Read → Edit → Bash(npm test)` appearing 8+ times → test-after-edit workflow skill
- `Grep → Read → Read → Edit` appearing 10+ times → search-and-fix workflow

If a multi-step sequence repeats and no skill covers it → gap candidate for a new skill or agent.

### Stack Coverage Gaps

Cross-reference the detected stack (from codebase-analyzer) against MCP servers in `.mcp.json`:
- Database in use (Postgres, MongoDB, etc.) but no database MCP server → gap
- Cloud provider in CI/CD config but no matching MCP → gap
- API framework detected but no API documentation MCP → gap

Reference: `${CLAUDE_PLUGIN_ROOT}/skills/mcp-advisor/references/mcp-catalog.md`

### Error Pattern Gaps

Recurring errors in session data suggest missing prevention hooks:
- Same error type appearing 3+ times → candidate for a hook that catches the pattern before it happens
- Permission denied errors → missing deny rules or overly broad permissions
- Build failures after edits → candidate for a pre-commit or pre-save hook

### File Co-Edit Gaps

Files edited together frequently suggest a specialized workflow:
- If 3+ files are always edited together → candidate for a skill that handles them as a unit
- If config files and code files are always paired → candidate for a "sync config" skill

## Bloat Detection

Bloat is things that exist but aren't being used. Before running bloat detection, verify the minimum session threshold.

**Read the heuristics**: `${CLAUDE_PLUGIN_ROOT}/skills/discover-analyzer/references/bloat-heuristics.md`

### Skill Usage Cross-Reference

For each skill in the inventory:
1. Search session assistant messages for the skill name
2. Check if session tool-call patterns match the skill's described workflow
3. Check if user messages contain the skill's trigger phrases

Zero matches across 15+ sessions → "potentially unused"

### MCP Server Usage Cross-Reference

For each MCP server in `.mcp.json`:
1. Count tool calls matching `mcp__<server-name>__*` in session data
2. Zero calls across 15+ sessions → "potentially unused"

### Agent Usage Cross-Reference

For each agent in the inventory:
1. Search for `Agent` tool_use blocks mentioning the agent name
2. Zero references across 15+ sessions → "potentially unused"

### Hook Activity Cross-Reference

For each hook:
1. Check if any session tool calls would match the hook's trigger pattern
2. If no session activity would ever trigger the hook → "potentially unnecessary"

### Redundancy Check

Compare all skill descriptions pairwise:
1. Tokenize into keywords, remove stop words
2. Calculate similarity (Jaccard or keyword overlap)
3. Flag pairs with >70% overlap as potentially redundant

### Safety Exemptions

**CRITICAL**: Never flag security-related items as bloat. Read the full exemption list in `${CLAUDE_PLUGIN_ROOT}/skills/discover-analyzer/references/security-constraints.md` under "Never Propose Removal Of."

## Balance Score

Calculate tooling coverage to help the user understand how much of their tooling is earning its context cost:

```
tooling_coverage = unique_tools_actually_used_in_sessions / total_tools_available
```

Where:
- **unique_tools_actually_used**: Count of distinct skills triggered, MCP tools called (`mcp__*`), and hooks that matched at least once across all analyzed sessions
- **total_tools_available**: Count of all configured skills + all MCP server tools + all hooks

This metric is stable regardless of how many sessions are analyzed (unlike a per-session ratio).

| Band | Range | Meaning |
|------|-------|---------|
| Low coverage | < 0.3 | Most tools unused — likely bloated or recently configured |
| Moderate coverage | 0.3 - 0.6 | Normal — some tools are situational |
| High coverage | 0.6 - 0.9 | Healthy — most tools earning their context cost |
| Full coverage | > 0.9 | Everything active — well-tuned or minimal setup |

Report the band and score, with a directional recommendation:
- Low coverage → "Many tools aren't being used — review for removal or check if skill descriptions need to be more aggressive about triggering"
- Moderate coverage → "Normal ratio — focus on filling gaps rather than adding more tools"
- High coverage → "Environment is well-tuned — most tools are earning their keep"
- Full coverage → "Everything is active — no bloat detected"

## Output Format

Return a structured analysis report:

```markdown
## Discovery Analysis

### Data Summary
- Sessions analyzed: N (date range)
- Session quality: N valid sessions after filtering
- Tooling density: X.X ([BAND])

### Gaps Found (N)
| # | Type | Evidence | Candidate |
|---|------|----------|-----------|
| 1 | Bash command | `npm test` ×47 | New hook or skill |
| 2 | Stack coverage | Postgres detected, no MCP | Install MCP |
| 3 | Error pattern | Build failure ×8 | Prevention hook |

### Bloat Found (N)
| # | Item | Type | Evidence | Confidence |
|---|------|------|----------|------------|
| 1 | unused-skill | Skill | 0 triggers in 25 sessions | Medium |
| 2 | old-mcp | MCP | 0 calls in 30 sessions | High |

### Redundancy Found (N)
| # | Item A | Item B | Overlap |
|---|--------|--------|---------|
| 1 | skill-a | skill-b | 78% description overlap |

### Balance Recommendation
[Direction based on tooling density band]
```
