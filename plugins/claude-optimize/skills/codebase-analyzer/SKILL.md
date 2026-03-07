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

Run all detection phases in parallel where possible. Use Glob and Read tools - avoid Bash unless necessary.

## Phase 1: Language & Framework Detection

Check for these indicators (check all in parallel):

### Package/Dependency Files
| File | Indicates |
|------|-----------|
| `package.json` | Node.js/JavaScript/TypeScript |
| `tsconfig.json` | TypeScript specifically |
| `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile` | Python |
| `Cargo.toml` | Rust |
| `go.mod` | Go |
| `Gemfile` | Ruby |
| `pom.xml`, `build.gradle`, `build.gradle.kts` | Java/Kotlin |
| `*.csproj`, `*.sln` | C#/.NET |
| `Package.swift` | Swift |
| `composer.json` | PHP |
| `mix.exs` | Elixir |
| `pubspec.yaml` | Dart/Flutter |

### Framework Detection
| Indicator | Framework |
|-----------|-----------|
| `next.config.*` | Next.js |
| `nuxt.config.*` | Nuxt |
| `angular.json` | Angular |
| `svelte.config.*` | SvelteKit |
| `remix.config.*` | Remix |
| `astro.config.*` | Astro |
| `vite.config.*` | Vite |
| `webpack.config.*` | Webpack |
| `django` in requirements | Django |
| `flask` in requirements | Flask |
| `fastapi` in requirements | FastAPI |
| `rails` in Gemfile | Ruby on Rails |
| `spring` in pom.xml | Spring Boot |
| `actix` or `axum` in Cargo.toml | Rust web framework |

### Package Manager Detection
| Indicator | Package Manager |
|-----------|-----------------|
| `bun.lock`, `bun.lockb` | bun |
| `pnpm-lock.yaml` | pnpm |
| `yarn.lock` | yarn |
| `package-lock.json` | npm |
| `uv.lock` | uv |
| `poetry.lock` | poetry |
| `Pipfile.lock` | pipenv |

### CI/CD Detection
| Indicator | CI/CD System |
|-----------|-------------|
| `.github/workflows/` | GitHub Actions |
| `.gitlab-ci.yml` | GitLab CI |
| `Jenkinsfile` | Jenkins |
| `.circleci/` | CircleCI |
| `.travis.yml` | Travis CI |
| `bitbucket-pipelines.yml` | Bitbucket Pipelines |

### Build/Test Tools
| Indicator | Tool |
|-----------|------|
| `jest.config.*`, `vitest.config.*` | Jest/Vitest |
| `pytest.ini`, `conftest.py`, `pyproject.toml` with pytest | pytest |
| `.eslintrc*`, `eslint.config.*` | ESLint |
| `.prettierrc*` | Prettier |
| `biome.json` | Biome |
| `Makefile` | Make |
| `Dockerfile`, `docker-compose.*` | Docker |
| `terraform/`, `*.tf` | Terraform |
| `k8s/`, `kubernetes/` | Kubernetes |

### External Services & APIs
| Indicator | Service | Informs |
|-----------|---------|---------|
| `stripe` in deps | Stripe payments | context7 MCP |
| `@aws-sdk/*` in deps | AWS infrastructure | AWS MCP |
| `@supabase/supabase-js` in deps | Supabase backend | Supabase MCP |
| `@sentry/*` in deps | Sentry error tracking | Sentry MCP |
| `@anthropic-ai/sdk` in deps | Anthropic API | context7 MCP |
| GitHub remote URL | GitHub hosting | GitHub MCP |
| Linear issue refs (ABC-123) | Linear issues | Linear MCP |
| Slack webhook URLs | Slack integration | Slack MCP |
| OpenAPI/Swagger specs | API documentation | API doc skills |

### Documentation Patterns
| Indicator | Pattern |
|-----------|---------|
| `openapi.yaml`, `swagger.json` | API documentation |
| JSDoc annotations | JavaScript docs |
| Docstrings in Python | Python docs |
| `docs/` directory | Documentation site |

## Phase 2: Claude Code Configuration Detection

Check for existing Claude Code setup:

### Configuration Files
- `.claude/settings.json` - permissions, hooks, deny rules
- `.claude/settings.local.json` - personal settings
- `CLAUDE.md` - project instructions (also check `.claude.md`, `.claude.local.md`)
- `.claude/commands/*.md` - existing commands
- `.claude/skills/*/SKILL.md` - existing skills
- `.claude/agents/*.md` - existing agents
- `.mcp.json` - MCP server configuration

### Memory Files
- `~/.claude/projects/` - find project-specific directory
- Check for `memory/` subdirectory with `.md` files
- Check for session logs (`*.jsonl` files)

### Installed Plugins
- Read `~/.claude/settings.json` for `enabledPlugins` list
- Check for plugin conflicts with claude-optimize

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
