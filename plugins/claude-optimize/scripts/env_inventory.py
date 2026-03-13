#!/usr/bin/env python3
"""Inventory all Claude Code environment components: skills, agents, hooks, MCP servers.

Catalogs everything currently configured in a Claude Code environment and outputs
a structured inventory. Replaces ad-hoc glob/read/parse instructions in discover.md
and other commands.
"""

import argparse
import glob
import json
import os
import re
import sys

# Add scripts dir to path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frontmatter_parser import parse_frontmatter


def find_skills(search_paths):
    """Find and catalog all skills from multiple search paths.

    Args:
        search_paths: List of directories to search for SKILL.md files

    Returns list of skill info dicts.
    """
    skills = []
    seen = set()

    for base_path in search_paths:
        base_path = os.path.expanduser(base_path)
        # Look for SKILL.md in subdirectories
        for skill_path in sorted(glob.glob(os.path.join(base_path, "*", "SKILL.md"))):
            skill_dir = os.path.dirname(skill_path)
            skill_name = os.path.basename(skill_dir)

            if skill_name in seen:
                continue
            seen.add(skill_name)

            fm = parse_frontmatter(skill_path)
            description = fm.get("description", "") if fm else ""
            word_count = len(description.split()) if description else 0

            skills.append({
                "name": skill_name,
                "description": description,
                "description_words": word_count,
                "source": base_path,
                "path": skill_path,
                "has_references": os.path.isdir(os.path.join(skill_dir, "references")),
                "has_scripts": os.path.isdir(os.path.join(skill_dir, "scripts")),
            })

    return skills


def find_agents(search_paths):
    """Find and catalog all agent definitions.

    Args:
        search_paths: List of directories to search for agent .md files

    Returns list of agent info dicts.
    """
    agents = []
    seen = set()

    for base_path in search_paths:
        base_path = os.path.expanduser(base_path)
        for agent_path in sorted(glob.glob(os.path.join(base_path, "*.md"))):
            agent_name = os.path.splitext(os.path.basename(agent_path))[0]

            if agent_name in seen:
                continue
            seen.add(agent_name)

            fm = parse_frontmatter(agent_path)
            description = fm.get("description", "") if fm else ""

            # Extract tools from frontmatter
            tools = fm.get("tools", "") if fm else ""

            agents.append({
                "name": agent_name,
                "description": description,
                "tools": tools,
                "source": base_path,
                "path": agent_path,
            })

    return agents


def find_hooks(settings_paths):
    """Find and catalog all hook configurations.

    Args:
        settings_paths: List of settings.json paths to check

    Returns list of hook info dicts.
    """
    hooks = []

    for settings_path in settings_paths:
        settings_path = os.path.expanduser(settings_path)
        if not os.path.isfile(settings_path):
            continue

        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Could not parse {settings_path}: {e}", file=sys.stderr)
            continue

        hook_config = settings.get("hooks", {})
        if not isinstance(hook_config, dict):
            continue

        for event_type, event_hooks in hook_config.items():
            if not isinstance(event_hooks, list):
                continue
            for hook_entry in event_hooks:
                if not isinstance(hook_entry, dict):
                    continue
                matcher = hook_entry.get("matcher", "")
                for hook in hook_entry.get("hooks", []):
                    if not isinstance(hook, dict):
                        continue
                    hooks.append({
                        "event": event_type,
                        "matcher": matcher,
                        "type": hook.get("type", "unknown"),
                        "command": hook.get("command", ""),
                        "timeout": hook.get("timeout"),
                        "source": settings_path,
                    })

    return hooks


def find_mcp_servers(mcp_paths):
    """Find and catalog all MCP server configurations.

    Args:
        mcp_paths: List of .mcp.json paths to check

    Returns list of MCP server info dicts.
    """
    servers = []

    for mcp_path in mcp_paths:
        mcp_path = os.path.expanduser(mcp_path)
        if not os.path.isfile(mcp_path):
            continue

        try:
            with open(mcp_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Could not parse {mcp_path}: {e}", file=sys.stderr)
            continue

        mcp_servers = config.get("mcpServers", {})
        if not isinstance(mcp_servers, dict):
            continue

        for name, server_config in mcp_servers.items():
            if not isinstance(server_config, dict):
                continue
            servers.append({
                "name": name,
                "command": server_config.get("command", ""),
                "args": server_config.get("args", []),
                "env": list(server_config.get("env", {}).keys()),
                "source": mcp_path,
            })

    return servers


def find_memory_files(project_dir=None):
    """Find and catalog all memory files.

    Args:
        project_dir: Claude project directory path

    Returns list of memory file info dicts.
    """
    memories = []

    if project_dir is None:
        # Try to find project dir
        cwd = os.getcwd()
        encoded = cwd.replace("/", "-").lstrip("-")
        project_dir = os.path.expanduser(f"~/.claude/projects/{encoded}")

    memory_dir = os.path.join(project_dir, "memory")
    if not os.path.isdir(memory_dir):
        return memories

    for mem_path in sorted(glob.glob(os.path.join(memory_dir, "*.md"))):
        fm = parse_frontmatter(mem_path)
        try:
            with open(mem_path, "r", encoding="utf-8") as f:
                content = f.read()
            lines = content.count("\n") + 1
            words = len(content.split())
        except OSError:
            lines = 0
            words = 0

        memories.append({
            "name": fm.get("name", os.path.basename(mem_path)) if fm else os.path.basename(mem_path),
            "type": fm.get("type", "unknown") if fm else "unknown",
            "description": fm.get("description", "") if fm else "",
            "path": mem_path,
            "lines": lines,
            "words": words,
            "tokens_estimated": int(words * 1.3),
        })

    # Also check for MEMORY.md
    memory_md = os.path.join(project_dir, "MEMORY.md")
    if os.path.isfile(memory_md):
        try:
            with open(memory_md, "r", encoding="utf-8") as f:
                content = f.read()
            lines = content.count("\n") + 1
            words = len(content.split())
        except OSError:
            lines = 0
            words = 0

        memories.insert(0, {
            "name": "MEMORY.md",
            "type": "index",
            "description": "Memory index file",
            "path": memory_md,
            "lines": lines,
            "words": words,
            "tokens_estimated": int(words * 1.3),
            "over_limit": lines > 200,
        })

    return memories


def build_full_inventory(project_root=None):
    """Build a complete environment inventory.

    Args:
        project_root: Root of the project (defaults to cwd)

    Returns dict with all components.
    """
    if project_root is None:
        project_root = os.getcwd()

    # Skill search paths
    skill_paths = [
        os.path.join(project_root, ".claude", "skills"),
        os.path.expanduser("~/.claude/skills"),
    ]
    # Also check plugin skills if CLAUDE_PLUGIN_ROOT is set
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if plugin_root:
        skill_paths.append(os.path.join(plugin_root, "skills"))

    # Agent search paths
    agent_paths = [
        os.path.join(project_root, ".claude", "agents"),
        os.path.expanduser("~/.claude/agents"),
    ]
    if plugin_root:
        agent_paths.append(os.path.join(plugin_root, "agents"))

    # Settings paths
    settings_paths = [
        os.path.join(project_root, ".claude", "settings.json"),
        os.path.expanduser("~/.claude/settings.json"),
    ]

    # MCP paths
    mcp_paths = [
        os.path.join(project_root, ".mcp.json"),
        os.path.expanduser("~/.mcp.json"),
    ]

    inventory = {
        "skills": find_skills(skill_paths),
        "agents": find_agents(agent_paths),
        "hooks": find_hooks(settings_paths),
        "mcp_servers": find_mcp_servers(mcp_paths),
        "memory_files": find_memory_files(),
    }

    # Add summary counts
    inventory["summary"] = {
        "total_skills": len(inventory["skills"]),
        "total_agents": len(inventory["agents"]),
        "total_hooks": len(inventory["hooks"]),
        "total_mcp_servers": len(inventory["mcp_servers"]),
        "total_memory_files": len(inventory["memory_files"]),
    }

    return inventory


def main():
    parser = argparse.ArgumentParser(
        description="Inventory Claude Code environment components"
    )
    parser.add_argument("--project-root", help="Project root directory (default: cwd)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--component",
        choices=["skills", "agents", "hooks", "mcp", "memory", "all"],
        default="all",
        help="Which component to inventory (default: all)",
    )
    args = parser.parse_args()

    inventory = build_full_inventory(args.project_root)

    if args.component != "all":
        key = "mcp_servers" if args.component == "mcp" else (
            "memory_files" if args.component == "memory" else args.component
        )
        filtered = {key: inventory[key]}
        inventory = filtered

    if args.json:
        print(json.dumps(inventory, indent=2))
    else:
        for section, items in inventory.items():
            if section == "summary":
                print(f"\n{'=' * 60}")
                print("SUMMARY")
                print(f"{'=' * 60}")
                for k, v in items.items():
                    print(f"  {k}: {v}")
                continue

            if not isinstance(items, list):
                continue

            print(f"\n{'=' * 60}")
            print(f"{section.upper()} ({len(items)} found)")
            print(f"{'=' * 60}")

            for item in items:
                name = item.get("name", "unknown")
                print(f"\n  [{name}]")
                for k, v in item.items():
                    if k == "name":
                        continue
                    if isinstance(v, list):
                        v = ", ".join(str(x) for x in v) if v else "(none)"
                    print(f"    {k}: {v}")


if __name__ == "__main__":
    main()
