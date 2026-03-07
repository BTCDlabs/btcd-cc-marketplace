# Bloat Detection Heuristics

Rules for determining when a skill, hook, MCP server, or agent should be flagged as potentially unused or redundant. These heuristics balance signal quality against false positives.

## Data Requirements

### Minimum Session Threshold

**15 sessions minimum** before flagging anything as unused. Below this threshold:
- Skip bloat detection entirely
- Note: "Insufficient session data for bloat analysis (N sessions found, 15 required)"
- Focus the discovery report on gap detection instead (which works from codebase analysis alone)

### Session Quality

Not all sessions are equal. Filter before analysis:
- Exclude sessions shorter than 2 minutes (likely test/abort sessions)
- Exclude sessions with fewer than 5 tool calls (not enough signal)
- Weight recent sessions higher than older ones (recency decay)

## Usage Detection Methods

### Skills

A skill is considered "used" if ANY of these are true across analyzed sessions:
1. The skill name appears in assistant message content (Claude mentions using it)
2. Tool-call patterns match the skill's described workflow (e.g., a "test-runner" skill and frequent `Bash(npm test)` calls)
3. The skill's trigger phrases appear in user messages that were followed by skill-relevant tool calls

**Zero across 15+ sessions** = "potentially unused"
**1-2 occurrences** = "low usage" (mention in report, don't recommend removal)

### MCP Servers

Count tool calls matching `mcp__<server-name>__*` pattern in session logs.

**Zero tool calls across 15+ sessions** = "potentially unused"
**1-5 tool calls** = "low usage" (mention, don't recommend removal)

### Agents

Search for `Agent` tool_use blocks where the prompt or description mentions the agent name.

**Zero references across 15+ sessions** = "potentially unused"

### Hooks

Harder to detect directly (hooks fire outside session transcripts). Instead:
- For PreToolUse hooks: check if any session tool calls match the hook's trigger pattern
- For Stop hooks: check if sessions show the hook's expected behavior
- If no session activity would ever trigger the hook = "potentially unnecessary"

## Exemptions

### Security Items (Never Flag)

These categories are **permanently exempt** from bloat detection, regardless of usage:

- Any hook containing keywords: `security`, `block`, `deny`, `sensitive`, `dangerous`, `protect`, `credential`, `secret`, `guard`
- Skills with "security" or "audit" in name or description
- Deny rules in settings files
- MCP servers providing security functionality

**Rationale**: Security tools are insurance. Low usage means things are working, not that the tool is unnecessary.

### Recently Added Items

Items created or modified within the last **30 days** get a pass:
- Check file modification time with `stat`
- Rationale: Not enough data to judge. The user may not have encountered the relevant workflow yet.

### Seasonal / Workflow-Specific Items

Some tools only trigger during specific workflows:
- Deploy/release skills → check for release branch names in session data
- CI/CD hooks → may only fire during specific pipeline interactions
- Migration tools → episodic by nature

**Detection**: If branch names in session data include patterns like `release/*`, `deploy/*`, `hotfix/*`, exempt tools related to those workflows from bloat detection.

## Redundancy Detection

### Description Overlap

Compare skill descriptions pairwise:
1. Tokenize descriptions into keywords (remove stop words)
2. Calculate Jaccard similarity: |intersection| / |union|
3. **>70% similarity** = flag as potentially redundant

Present both skills and let the user decide which to keep.

### Functional Overlap

A skill and an MCP server covering the same capability:
- E.g., a "database-query" skill and an MCP server with SQL tools
- Flag as "overlapping" — present as alternatives, not automatic removals

## Confidence Levels

Present bloat findings with confidence:

| Sessions | Zero Usage Confidence | Recommendation |
|----------|-----------------------|----------------|
| 15-25 | Low | "May be unused — monitor" |
| 25-50 | Medium | "Likely unused — consider removal" |
| 50+ | High | "Unused — recommend removal" |

## Plugin vs. User-Created

**Plugin-provided items** (from installed plugins):
- Higher bar for removal (someone built and published this)
- Suggest disabling over removing
- Note: removing a plugin item may be undone on plugin update

**User-created items** (in .claude/skills/, .claude/hooks/, etc.):
- Standard bar for removal
- Can be deleted directly
- Note: suggest backing up before removal

## Reporting Format

Present bloat findings in this structure:

```markdown
### Bloat Analysis

**Data quality**: N sessions analyzed (threshold: 15) — confidence: [LOW|MEDIUM|HIGH]

#### Potentially Unused
| Item | Type | Source | Last Used | Sessions Checked | Confidence |
|------|------|--------|-----------|------------------|------------|
| ... | Skill | project | never | 25 | Medium |

#### Low Usage
| Item | Type | Usage Count | Sessions Checked |
|------|------|-------------|------------------|
| ... | MCP | 2 calls | 30 |

#### Redundancy
| Item A | Item B | Overlap | Recommendation |
|--------|--------|---------|----------------|
| ... | ... | 75% description | Keep one |
```
