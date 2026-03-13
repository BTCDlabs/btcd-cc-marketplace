# btcd-cc-marketplace

A marketplace for internal BTCD Claude Code plugins.

## Overview

This repository hosts Claude Code plugins developed and maintained by BTCD. Plugins are distributed via the Claude Code marketplace plugin system.

## Plugins

| Plugin | Version | Description |
|--------|---------|-------------|
| [claude-optimize](plugins/claude-optimize/) | 0.3.5 | Meta-plugin for recursive self-improvement of Claude Code environments. Provides 11 optimization modes for analyzing and improving your setup. |

## Installation

Install a plugin from this marketplace inside a Claude Code session:

```
/plugin install claude-optimize@btcd-cc-marketplace
```

Or load locally for development:

```bash
claude --plugin-dir /path/to/btcd-cc-marketplace/plugins/claude-optimize
```

## Repository Structure

```
.claude-plugin/
  marketplace.json          # Marketplace metadata and plugin registry
plugins/
  claude-optimize/          # Optimization meta-plugin
    .claude-plugin/
      plugin.json           # Plugin metadata
    agents/                 # Specialized agent definitions
    commands/               # Slash command definitions
    hooks/                  # Hook scripts (e.g., optimization loop)
    skills/                 # Skill definitions and reference docs
    README.md               # Plugin-specific documentation
```

## Maintainer

Hunter Prendergast (hunter.prendergast@btcd.fi)

## License

MIT
