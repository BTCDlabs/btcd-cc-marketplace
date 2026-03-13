---
name: codebase-analyzer
description: >
  Use when running /optimize:init or /optimize:audit to detect project type, language,
  framework, package manager, CI/CD system, and existing Claude Code configuration.
  Triggers on codebase analysis for optimization, project detection for Claude Code setup,
  or environment assessment. Do NOT trigger on general coding tasks.
---

# Codebase Analyzer

Analyzes a project's codebase to detect its technology stack, existing Claude Code configuration, and optimization opportunities. This skill powers the detection phase of `/optimize:init` and `/optimize:audit`.

## Detection Strategy

ALWAYS use the bundled script for codebase detection. Do NOT manually check file patterns or parse dependency files.

## Phase 1: Technology Stack Detection

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/codebase_detector.py --json
```

The script automatically detects:
- **Languages**: From dependency/config files (package.json, requirements.txt, Cargo.toml, go.mod, etc.)
- **Frameworks**: From config files (next.config.*, angular.json, etc.) and dependency contents (django, flask, spring, etc.)
- **Package Managers**: From lock files (bun.lock, yarn.lock, package-lock.json, etc.)
- **CI/CD**: From config files (.github/workflows/, .gitlab-ci.yml, Jenkinsfile, etc.)
- **Build/Test Tools**: Jest, pytest, ESLint, Prettier, Docker, Make, etc.
- **External Services**: Stripe, AWS, Supabase, Sentry, etc. with MCP server suggestions
- **Claude Code Config**: CLAUDE.md files, settings, commands, skills, agents, MCP servers, plugins

## Phase 2: Environment Inventory

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/env_inventory.py --json
```

The script catalogs all existing Claude Code components: skills, agents, hooks, MCP servers, and memory files.

## Phase 3: Output Format

Present findings as a structured assessment:

```markdown
## Project Profile

**Language**: [primary language]
**Framework**: [if detected]
**Package Manager**: [detected PM]
**CI/CD**: [if detected]
**Test Framework**: [if detected]
**Linter/Formatter**: [if detected]

## Claude Code Status

| Component | Status | Details |
|-----------|--------|---------|
| CLAUDE.md | present/missing | [line count, token estimate] |
| Settings | present/missing | [# allow rules, # deny rules] |
| Commands | [count] | [list names] |
| Skills | [count] | [list names] |
| Agents | [count] | [list names] |
| Hooks | [count] | [types configured] |
| MCP Servers | [count] | [list names] |
| Memory Files | [count] | [total size] |
| Session Logs | [count] | [date range] |

## Recommendations

[Based on detected stack, recommend specific optimizations]
```
