# MCP Server Catalog

Recommended MCP servers organized by detection signal. Use web search for servers specific to the codebase's services.

## Setup

**Connection methods:**
1. **Project config** (`.mcp.json`) - Available only in that directory
2. **Global config** (`~/.claude.json`) - Available across all projects
3. **Checked-in `.mcp.json`** - Available to entire team (recommended)

**Tip**: Check `.mcp.json` into git so your whole team gets the same MCP servers.

**Debugging**: `claude --mcp-debug` to identify configuration issues.

## Documentation & Knowledge

### context7
**Best for**: Projects using popular libraries/SDKs

| Detection Signal | Examples |
|-----------------|----------|
| React, Vue, Angular, Next.js | Frontend frameworks |
| Express, FastAPI, Django | Backend frameworks |
| Prisma, Drizzle | ORMs |
| Stripe, Twilio, SendGrid | Third-party APIs |
| AWS SDK, Google Cloud | Cloud SDKs |
| LangChain, Anthropic SDK | AI/ML libraries |

**Value**: Live documentation instead of training data.

## Browser & Frontend

### Playwright MCP
| Detection Signal | Use Case |
|-----------------|----------|
| React/Vue/Angular app | UI testing |
| E2E tests needed | User flow validation |
| Visual regression | Screenshot comparisons |
| Debugging UI issues | See what user sees |
| Form testing | Multi-step workflows |

### Puppeteer MCP
| Detection Signal | Use Case |
|-----------------|----------|
| PDF generation from HTML | Report generation |
| Web scraping tasks | Data extraction |
| Headless testing | CI environments |

## Databases

### Supabase MCP
| Detection Signal | Use Case |
|-----------------|----------|
| `@supabase/supabase-js` in deps | Database + auth |

### PostgreSQL MCP
| Detection Signal | Use Case |
|-----------------|----------|
| `pg` or `postgres` in deps | Direct DB access |
| Database migrations | Schema management |
| Data analysis tasks | Complex queries |

### Neon MCP
| Detection Signal | Use Case |
|-----------------|----------|
| Neon serverless Postgres | Edge database |

### Turso MCP
| Detection Signal | Use Case |
|-----------------|----------|
| Turso/libSQL usage | Edge SQLite database |

## Version Control & DevOps

### GitHub MCP
| Detection Signal | Use Case |
|-----------------|----------|
| GitHub remote URL | Issue/PR management |
| GitHub Actions | CI/CD pipeline access |
| Release management | Tag and release automation |

### GitLab MCP
| Detection Signal | Use Case |
|-----------------|----------|
| GitLab remote URL | GitLab-hosted repos |

### Linear MCP
| Detection Signal | Use Case |
|-----------------|----------|
| Linear issue refs (ABC-123) | Issue tracking |

## Cloud Infrastructure

### AWS MCP
| Detection Signal | Use Case |
|-----------------|----------|
| `@aws-sdk/*` packages | AWS management |

### Cloudflare MCP
| Detection Signal | Use Case |
|-----------------|----------|
| Cloudflare Workers | Edge functions |
| Pages deployment | Static site hosting |
| R2 storage | Object storage |
| D1 database | Edge SQL database |

### Vercel MCP
| Detection Signal | Use Case |
|-----------------|----------|
| `vercel.json`, Vercel deployment | Deployment + config |

## Monitoring

### Sentry MCP
| Detection Signal | Use Case |
|-----------------|----------|
| `@sentry/*` in deps | Error tracking |
| Production debugging | Investigate errors |
| Release tracking | Correlate deploys with errors |

### Datadog MCP
| Detection Signal | Use Case |
|-----------------|----------|
| Datadog config/deps | APM, logs, and metrics |

## Containers

### Docker MCP
| Detection Signal | Use Case |
|-----------------|----------|
| `docker-compose.yml`, Dockerfile | Container management |

### Kubernetes MCP
| Detection Signal | Use Case |
|-----------------|----------|
| K8s manifests, Helm charts | Cluster management |

## Communication

### Slack MCP
| Detection Signal | Use Case |
|-----------------|----------|
| Team uses Slack | Send notifications |
| Deployment notifications | Alert channels |
| Incident response | Post updates |

### Notion MCP
| Detection Signal | Use Case |
|-----------------|----------|
| Notion for docs | Read/update pages |
| Knowledge base | Search documentation |

## File & Data

### Filesystem MCP
| Detection Signal | Use Case |
|-----------------|----------|
| Complex file operations | Batch processing |
| File watching | Monitor changes |

### Memory MCP
| Detection Signal | Use Case |
|-----------------|----------|
| Long-running projects | Remember context |
| User preferences | Store settings |

**Value**: Claude remembers project context, decisions, and patterns across conversations.

## Research

### Exa MCP
| Detection Signal | Use Case |
|-----------------|----------|
| Research tasks | Find current info |
| Documentation gaps | Find examples |

## Quick Detection Reference

| Look For | Suggests MCP Server |
|----------|-------------------|
| Popular npm packages | context7 |
| React/Vue/Next.js | Playwright MCP |
| PDF generation, scraping | Puppeteer MCP |
| `@supabase/supabase-js` | Supabase MCP |
| `pg` or `postgres` | PostgreSQL MCP |
| Neon serverless Postgres | Neon MCP |
| Turso/libSQL | Turso MCP |
| GitHub remote | GitHub MCP |
| GitLab remote | GitLab MCP |
| Linear refs | Linear MCP |
| `@aws-sdk/*` | AWS MCP |
| Cloudflare Workers/Pages | Cloudflare MCP |
| `vercel.json` | Vercel MCP |
| `@sentry/*` | Sentry MCP |
| Datadog config | Datadog MCP |
| `docker-compose.yml` | Docker MCP |
| K8s manifests | Kubernetes MCP |
| Slack webhooks | Slack MCP |
| Notion workspace | Notion MCP |
| `@anthropic-ai/sdk` | context7 for Anthropic docs |
