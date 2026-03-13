#!/usr/bin/env python3
"""Health check MCP servers configured in .mcp.json.

Validates:
- Command existence (via `which` / `command -v`)
- Required environment variables are set
- Configuration completeness
- Estimates tool count per server from catalog

Replaces ad-hoc health check instructions in mcp-advisor/SKILL.md.
"""

import argparse
import json
import os
import subprocess
import sys


# Known MCP servers and their expected tool counts (from mcp-catalog.md)
KNOWN_SERVERS = {
    "filesystem": {"tools": 11, "category": "filesystem"},
    "github": {"tools": 15, "category": "development"},
    "gitlab": {"tools": 12, "category": "development"},
    "slack": {"tools": 8, "category": "communication"},
    "postgres": {"tools": 6, "category": "database"},
    "sqlite": {"tools": 5, "category": "database"},
    "puppeteer": {"tools": 7, "category": "browser"},
    "brave-search": {"tools": 2, "category": "search"},
    "fetch": {"tools": 1, "category": "network"},
    "memory": {"tools": 4, "category": "knowledge"},
    "sequential-thinking": {"tools": 1, "category": "reasoning"},
    "google-maps": {"tools": 5, "category": "geolocation"},
    "sentry": {"tools": 4, "category": "monitoring"},
    "linear": {"tools": 10, "category": "project-management"},
    "notion": {"tools": 8, "category": "knowledge"},
    "docker": {"tools": 8, "category": "infrastructure"},
    "kubernetes": {"tools": 12, "category": "infrastructure"},
    "aws": {"tools": 15, "category": "cloud"},
    "gcp": {"tools": 12, "category": "cloud"},
    "etherscan": {"tools": 20, "category": "blockchain"},
}

# Token cost estimates
TOKENS_PER_TOOL_ALWAYS = 150  # Always-loaded tools
TOKENS_PER_TOOL_DEFERRED = 20  # Deferred tools (just name)


def load_mcp_config(mcp_path):
    """Load MCP configuration from .mcp.json file."""
    mcp_path = os.path.expanduser(mcp_path)
    if not os.path.isfile(mcp_path):
        return None

    try:
        with open(mcp_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error reading {mcp_path}: {e}", file=sys.stderr)
        return None


def check_command_exists(command):
    """Check if a command exists on the system."""
    try:
        result = subprocess.run(
            ["which", command],
            capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_env_vars(env_config):
    """Check which environment variables from config are actually set."""
    results = {}
    if not isinstance(env_config, dict):
        return results
    for var_name in env_config:
        results[var_name] = os.environ.get(var_name) is not None
    return results


def estimate_tool_count(server_name, server_config):
    """Estimate tool count for a server based on catalog or heuristics."""
    # Check known servers first
    for known_name, info in KNOWN_SERVERS.items():
        if known_name in server_name.lower():
            return info["tools"], "catalog"

    # Check args for clues (e.g., model names, capability flags)
    args = server_config.get("args", [])
    if isinstance(args, list) and len(args) > 0:
        # Heuristic: more args often means more capabilities
        return min(5 + len(args), 20), "heuristic"

    return 5, "default"  # Conservative default


def check_server_health(name, config):
    """Run health checks on a single MCP server.

    Returns dict with health status and issues.
    """
    issues = []
    checks = {}

    # Check command exists
    command = config.get("command", "")
    if command:
        exists = check_command_exists(command)
        checks["command_exists"] = exists
        if not exists:
            issues.append({
                "severity": "critical",
                "message": f"Command '{command}' not found on system",
            })
    else:
        checks["command_exists"] = False
        issues.append({
            "severity": "critical",
            "message": "No command specified in server config",
        })

    # Check environment variables
    env_config = config.get("env", {})
    if env_config:
        env_status = check_env_vars(env_config)
        checks["env_vars"] = env_status
        for var, is_set in env_status.items():
            if not is_set:
                issues.append({
                    "severity": "high",
                    "message": f"Required env var '{var}' is not set",
                })

    # Check args
    args = config.get("args", [])
    checks["has_args"] = bool(args)

    # Estimate tool count
    tool_count, source = estimate_tool_count(name, config)
    checks["estimated_tools"] = tool_count
    checks["tool_count_source"] = source

    # Calculate token impact
    token_impact = tool_count * TOKENS_PER_TOOL_ALWAYS
    checks["token_impact_always"] = token_impact
    checks["token_impact_deferred"] = tool_count * TOKENS_PER_TOOL_DEFERRED

    # Determine overall status
    critical_count = sum(1 for i in issues if i["severity"] == "critical")
    high_count = sum(1 for i in issues if i["severity"] == "high")

    if critical_count > 0:
        status = "unhealthy"
    elif high_count > 0:
        status = "degraded"
    else:
        status = "healthy"

    return {
        "name": name,
        "command": command,
        "status": status,
        "checks": checks,
        "issues": issues,
    }


def check_trust_settings(settings_path=None):
    """Check MCP trust-related settings in settings.json.

    Returns dict with trust assessment findings.
    """
    if settings_path is None:
        settings_path = ".claude/settings.json"

    settings_path = os.path.expanduser(settings_path)
    findings = {
        "enableAllProjectMcpServers": False,
        "settings_path": settings_path,
        "issues": [],
    }

    if not os.path.isfile(settings_path):
        return findings

    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except (json.JSONDecodeError, OSError):
        return findings

    # Check enableAllProjectMcpServers
    if settings.get("enableAllProjectMcpServers", False):
        findings["enableAllProjectMcpServers"] = True
        findings["issues"].append({
            "severity": "critical",
            "message": "enableAllProjectMcpServers is true - all project MCP servers auto-trusted",
        })

    return findings


def analyze_mcp_config(mcp_path, settings_path=None):
    """Analyze complete MCP configuration.

    Returns dict with per-server health and aggregate metrics.
    """
    config = load_mcp_config(mcp_path)
    if config is None:
        return {"error": f"Could not load {mcp_path}", "servers": []}

    servers_config = config.get("mcpServers", {})
    if not isinstance(servers_config, dict):
        return {"error": "No mcpServers found in config", "servers": []}

    results = []
    total_tools = 0
    total_token_impact = 0

    for name, server_config in servers_config.items():
        if not isinstance(server_config, dict):
            continue
        health = check_server_health(name, server_config)
        results.append(health)
        total_tools += health["checks"].get("estimated_tools", 0)
        total_token_impact += health["checks"].get("token_impact_always", 0)

    healthy = sum(1 for r in results if r["status"] == "healthy")
    degraded = sum(1 for r in results if r["status"] == "degraded")
    unhealthy = sum(1 for r in results if r["status"] == "unhealthy")

    # Score (0-100)
    if not results:
        score = 100  # No servers = no issues
    else:
        score = int((healthy / len(results)) * 80 + (degraded / len(results)) * 40)
        if total_tools > 50:
            score -= 10  # Penalty for excessive tool count
        score = max(0, min(100, score))

    # Check trust settings
    trust = check_trust_settings(settings_path)
    if trust["enableAllProjectMcpServers"]:
        score = max(0, score - 20)  # Heavy penalty

    return {
        "mcp_path": mcp_path,
        "servers": results,
        "trust": trust,
        "summary": {
            "total_servers": len(results),
            "healthy": healthy,
            "degraded": degraded,
            "unhealthy": unhealthy,
            "total_estimated_tools": total_tools,
            "total_token_impact": total_token_impact,
            "score": score,
            "grade": _grade(score),
        },
    }


def _grade(score):
    """Convert score to grade."""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    return "F"


def main():
    parser = argparse.ArgumentParser(description="Health check MCP servers")
    parser.add_argument(
        "mcp_paths", nargs="*",
        default=[".mcp.json", os.path.expanduser("~/.mcp.json")],
        help="Paths to .mcp.json files (default: project + user)",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--summary", action="store_true", help="With --json, output only summaries")
    parser.add_argument(
        "--server", metavar="NAME",
        help="Check only this specific server"
    )
    args = parser.parse_args()

    all_results = []
    for mcp_path in args.mcp_paths:
        result = analyze_mcp_config(mcp_path)
        all_results.append(result)

    if args.json:
        if args.summary:
            print(json.dumps([r.get("summary", {}) for r in all_results], indent=2))
        else:
            print(json.dumps(all_results, indent=2))
    else:
        for result in all_results:
            path = result.get("mcp_path", "unknown")
            print(f"\n{'=' * 60}")
            print(f"MCP HEALTH CHECK: {path}")
            print(f"{'=' * 60}")

            if "error" in result:
                print(f"  {result['error']}")
                continue

            summary = result.get("summary", {})
            print(f"\n  Score: {summary.get('score', 0)}/100 (Grade: {summary.get('grade', 'F')})")
            print(f"  Servers: {summary.get('total_servers', 0)} "
                  f"(healthy: {summary.get('healthy', 0)}, "
                  f"degraded: {summary.get('degraded', 0)}, "
                  f"unhealthy: {summary.get('unhealthy', 0)})")
            print(f"  Estimated tools: {summary.get('total_estimated_tools', 0)}")
            print(f"  Token impact: ~{summary.get('total_token_impact', 0)} tokens")

            for server in result.get("servers", []):
                if args.server and server["name"] != args.server:
                    continue
                status_icon = {"healthy": "OK", "degraded": "WARN", "unhealthy": "FAIL"}
                print(f"\n  [{status_icon.get(server['status'], '??'):4s}] {server['name']}")
                print(f"    Command: {server['command']}")
                print(f"    Est. tools: {server['checks'].get('estimated_tools', '?')} "
                      f"({server['checks'].get('tool_count_source', '?')})")

                for issue in server.get("issues", []):
                    print(f"    [{issue['severity'].upper()}] {issue['message']}")


if __name__ == "__main__":
    main()
