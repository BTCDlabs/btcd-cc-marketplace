# MCP Server Security Checklist

Security evaluation criteria for MCP servers configured in `.mcp.json`.

## Per-Server Checks

### 1. Transport Security

| Check | Pass | Fail |
|-------|------|------|
| Uses HTTPS for remote connections | HTTPS URL | HTTP URL |
| Local servers use stdio or localhost | stdio/127.0.0.1 | 0.0.0.0 binding |
| No plain-text credentials in URLs | Clean URLs | Tokens in URL params |

### 2. Authentication

| Check | Pass | Fail |
|-------|------|------|
| API keys via environment variables | `${API_KEY}` | Hardcoded key in config |
| Credentials not in version control | In .env or env vars | In .mcp.json directly |
| Tokens have appropriate scopes | Read-only where possible | Admin/write tokens |

### 3. Trust Verification

| Trust Level | Criteria |
|-------------|----------|
| **High** | Official vendor server (e.g., Anthropic, GitHub, Stripe), well-known open source with >1000 stars |
| **Medium** | Recognized open source project, audited code, active maintenance |
| **Low** | Unknown author, few stars, no audit history, recently created |
| **Untrusted** | Forked from known project with modifications, obfuscated code, excessive permissions |

### 4. Scope Assessment

| Check | Pass | Fail |
|-------|------|------|
| Exposes only needed tools | Focused tool set | Kitchen-sink tool exposure |
| No file system write access (unless needed) | Read-only | Write access to arbitrary paths |
| No network access beyond stated purpose | Scoped networking | Arbitrary outbound connections |
| No shell execution capability | No exec tools | Can run arbitrary commands |

### 5. Configuration Security

| Check | Pass | Fail |
|-------|------|------|
| `enableAllProjectMcpServers` is false | false/absent | true |
| Server args don't contain secrets | Clean args | Secrets in args array |
| Environment variables properly sourced | From env/vault | Hardcoded values |

## Global Checks

### enableAllProjectMcpServers

**Risk**: If `true`, any MCP server defined in any project's `.mcp.json` starts automatically when Claude Code opens that project. A malicious repo could include an `.mcp.json` that starts a compromised server.

**Recommendation**: Always keep this `false`. Explicitly enable only trusted servers.

### Server Count Impact

Each MCP server adds tools to Claude's context:
- 1-3 servers: Low impact
- 4-7 servers: Moderate impact (consider deferred loading)
- 8+ servers: High impact (significant context consumption)

## Common MCP Servers - Trust Assessment

| Server | Trust | Notes |
|--------|-------|-------|
| `@anthropic/claude-code-mcp` | High | Official Anthropic server |
| `@modelcontextprotocol/server-github` | High | Official MCP org |
| `@modelcontextprotocol/server-filesystem` | High | Official, but scope file access |
| `@modelcontextprotocol/server-slack` | High | Official MCP org |
| Community servers | Verify | Check stars, maintenance, code audit |

## Remediation Actions

### For untrusted servers:
1. Remove from `.mcp.json`
2. Audit what data the server had access to
3. Rotate any credentials the server could have observed

### For insecure configuration:
1. Move secrets to environment variables
2. Switch to HTTPS where available
3. Reduce token scopes to minimum needed
4. Set `enableAllProjectMcpServers: false`
