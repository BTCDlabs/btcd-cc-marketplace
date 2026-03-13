#!/usr/bin/env python3
"""Detect project technology stack from file indicators.

Replaces ad-hoc file-pattern-checking tables in codebase-analyzer/SKILL.md.
Checks for language indicators, frameworks, package managers, CI/CD, build tools,
external services, and existing Claude Code configuration.
"""

import argparse
import glob
import json
import os
import re
import sys


# Language detection via dependency/config files
LANGUAGE_INDICATORS = {
    "package.json": "JavaScript/TypeScript",
    "tsconfig.json": "TypeScript",
    "requirements.txt": "Python",
    "pyproject.toml": "Python",
    "setup.py": "Python",
    "Pipfile": "Python",
    "Cargo.toml": "Rust",
    "go.mod": "Go",
    "Gemfile": "Ruby",
    "pom.xml": "Java",
    "build.gradle": "Java/Kotlin",
    "build.gradle.kts": "Kotlin",
    "Package.swift": "Swift",
    "composer.json": "PHP",
    "mix.exs": "Elixir",
    "pubspec.yaml": "Dart/Flutter",
}

# Framework detection via config files
FRAMEWORK_FILE_INDICATORS = {
    "next.config.*": "Next.js",
    "nuxt.config.*": "Nuxt",
    "angular.json": "Angular",
    "svelte.config.*": "SvelteKit",
    "remix.config.*": "Remix",
    "astro.config.*": "Astro",
    "vite.config.*": "Vite",
    "webpack.config.*": "Webpack",
}

# Framework detection via dependency contents
FRAMEWORK_DEP_INDICATORS = {
    "django": {"file": "requirements.txt", "framework": "Django"},
    "flask": {"file": "requirements.txt", "framework": "Flask"},
    "fastapi": {"file": "requirements.txt", "framework": "FastAPI"},
    "rails": {"file": "Gemfile", "framework": "Ruby on Rails"},
    "spring": {"file": "pom.xml", "framework": "Spring Boot"},
    "actix": {"file": "Cargo.toml", "framework": "Actix"},
    "axum": {"file": "Cargo.toml", "framework": "Axum"},
}

# Package manager detection
PACKAGE_MANAGER_INDICATORS = {
    "bun.lock": "bun",
    "bun.lockb": "bun",
    "pnpm-lock.yaml": "pnpm",
    "yarn.lock": "yarn",
    "package-lock.json": "npm",
    "uv.lock": "uv",
    "poetry.lock": "poetry",
    "Pipfile.lock": "pipenv",
}

# CI/CD detection
CICD_INDICATORS = {
    ".github/workflows/": "GitHub Actions",
    ".gitlab-ci.yml": "GitLab CI",
    "Jenkinsfile": "Jenkins",
    ".circleci/": "CircleCI",
    ".travis.yml": "Travis CI",
    "bitbucket-pipelines.yml": "Bitbucket Pipelines",
}

# Build/test tool detection
BUILD_TOOL_INDICATORS = {
    "jest.config.*": "Jest",
    "vitest.config.*": "Vitest",
    "pytest.ini": "pytest",
    "conftest.py": "pytest",
    ".eslintrc*": "ESLint",
    "eslint.config.*": "ESLint",
    ".prettierrc*": "Prettier",
    "biome.json": "Biome",
    "Makefile": "Make",
    "Dockerfile": "Docker",
    "docker-compose.*": "Docker Compose",
}

# External service detection via deps
SERVICE_INDICATORS = {
    "stripe": {"service": "Stripe", "mcp_suggestion": "context7"},
    "@aws-sdk": {"service": "AWS", "mcp_suggestion": "aws"},
    "@supabase/supabase-js": {"service": "Supabase", "mcp_suggestion": "supabase"},
    "@sentry": {"service": "Sentry", "mcp_suggestion": "sentry"},
    "@anthropic-ai/sdk": {"service": "Anthropic API", "mcp_suggestion": "context7"},
}


def _file_exists(project_root, pattern):
    """Check if a file or glob pattern exists relative to project root."""
    if "*" in pattern:
        matches = glob.glob(os.path.join(project_root, pattern))
        return len(matches) > 0
    path = os.path.join(project_root, pattern)
    return os.path.exists(path)


def _read_file_safe(filepath):
    """Read file content, return empty string on failure."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return ""


def detect_languages(project_root):
    """Detect programming languages used in the project."""
    languages = []
    for indicator, language in LANGUAGE_INDICATORS.items():
        if _file_exists(project_root, indicator):
            languages.append({"language": language, "indicator": indicator})
    return languages


def detect_frameworks(project_root):
    """Detect frameworks used in the project."""
    frameworks = []

    # File-based detection
    for pattern, framework in FRAMEWORK_FILE_INDICATORS.items():
        if _file_exists(project_root, pattern):
            frameworks.append({"framework": framework, "indicator": pattern})

    # Dependency-content-based detection
    for keyword, info in FRAMEWORK_DEP_INDICATORS.items():
        dep_file = os.path.join(project_root, info["file"])
        if os.path.isfile(dep_file):
            content = _read_file_safe(dep_file)
            if keyword.lower() in content.lower():
                frameworks.append({
                    "framework": info["framework"],
                    "indicator": f"{keyword} in {info['file']}",
                })

    return frameworks


def detect_package_manager(project_root):
    """Detect package managers from lock files."""
    managers = []
    for indicator, manager in PACKAGE_MANAGER_INDICATORS.items():
        if _file_exists(project_root, indicator):
            managers.append({"manager": manager, "indicator": indicator})
    return managers


def detect_cicd(project_root):
    """Detect CI/CD systems."""
    systems = []
    for indicator, system in CICD_INDICATORS.items():
        if indicator.endswith("/"):
            if os.path.isdir(os.path.join(project_root, indicator.rstrip("/"))):
                systems.append({"system": system, "indicator": indicator})
        elif _file_exists(project_root, indicator):
            systems.append({"system": system, "indicator": indicator})
    return systems


def detect_build_tools(project_root):
    """Detect build and test tools."""
    tools = []
    seen = set()
    for pattern, tool in BUILD_TOOL_INDICATORS.items():
        if tool in seen:
            continue
        if _file_exists(project_root, pattern):
            tools.append({"tool": tool, "indicator": pattern})
            seen.add(tool)

    # Also check pyproject.toml for pytest config
    pyproject = os.path.join(project_root, "pyproject.toml")
    if os.path.isfile(pyproject) and "pytest" not in seen:
        content = _read_file_safe(pyproject)
        if "[tool.pytest" in content:
            tools.append({"tool": "pytest", "indicator": "pyproject.toml [tool.pytest]"})

    return tools


def detect_services(project_root):
    """Detect external services from dependency files."""
    services = []
    seen = set()

    # Check package.json
    pkg_path = os.path.join(project_root, "package.json")
    if os.path.isfile(pkg_path):
        content = _read_file_safe(pkg_path)
        for keyword, info in SERVICE_INDICATORS.items():
            if keyword in content and info["service"] not in seen:
                services.append({
                    "service": info["service"],
                    "indicator": f"{keyword} in package.json",
                    "mcp_suggestion": info["mcp_suggestion"],
                })
                seen.add(info["service"])

    # Check requirements.txt
    req_path = os.path.join(project_root, "requirements.txt")
    if os.path.isfile(req_path):
        content = _read_file_safe(req_path)
        for keyword, info in SERVICE_INDICATORS.items():
            kw = keyword.lstrip("@").split("/")[0]
            if kw in content and info["service"] not in seen:
                services.append({
                    "service": info["service"],
                    "indicator": f"{kw} in requirements.txt",
                    "mcp_suggestion": info["mcp_suggestion"],
                })
                seen.add(info["service"])

    # Check for GitHub remote
    git_config = os.path.join(project_root, ".git", "config")
    if os.path.isfile(git_config):
        content = _read_file_safe(git_config)
        if "github.com" in content and "GitHub" not in seen:
            services.append({
                "service": "GitHub",
                "indicator": "git remote",
                "mcp_suggestion": "github",
            })

    return services


def detect_claude_config(project_root):
    """Detect existing Claude Code configuration."""
    config = {
        "claude_md": [],
        "settings": [],
        "commands": [],
        "skills": [],
        "agents": [],
        "mcp_config": None,
        "memory_dir": None,
        "plugins": [],
    }

    # CLAUDE.md files
    for name in ["CLAUDE.md", ".claude.md", ".claude.local.md"]:
        path = os.path.join(project_root, name)
        if os.path.isfile(path):
            size = os.path.getsize(path)
            config["claude_md"].append({"file": name, "size_bytes": size})

    # Settings files
    for name in ["settings.json", "settings.local.json"]:
        path = os.path.join(project_root, ".claude", name)
        if os.path.isfile(path):
            config["settings"].append(name)

    # Commands
    cmd_dir = os.path.join(project_root, ".claude", "commands")
    if os.path.isdir(cmd_dir):
        for f in os.listdir(cmd_dir):
            if f.endswith(".md"):
                config["commands"].append(f)

    # Skills
    skill_dir = os.path.join(project_root, ".claude", "skills")
    if os.path.isdir(skill_dir):
        for d in os.listdir(skill_dir):
            skill_path = os.path.join(skill_dir, d, "SKILL.md")
            if os.path.isfile(skill_path):
                config["skills"].append(d)

    # Agents
    agent_dir = os.path.join(project_root, ".claude", "agents")
    if os.path.isdir(agent_dir):
        for f in os.listdir(agent_dir):
            if f.endswith(".md"):
                config["agents"].append(os.path.splitext(f)[0])

    # MCP config
    mcp_path = os.path.join(project_root, ".mcp.json")
    if os.path.isfile(mcp_path):
        try:
            with open(mcp_path, "r") as f:
                mcp = json.load(f)
            servers = list(mcp.get("mcpServers", {}).keys())
            config["mcp_config"] = {"path": ".mcp.json", "servers": servers}
        except (json.JSONDecodeError, OSError):
            config["mcp_config"] = {"path": ".mcp.json", "error": "parse failed"}

    # Installed plugins
    user_settings = os.path.expanduser("~/.claude/settings.json")
    if os.path.isfile(user_settings):
        try:
            with open(user_settings, "r") as f:
                us = json.load(f)
            config["plugins"] = us.get("enabledPlugins", [])
        except (json.JSONDecodeError, OSError):
            pass

    return config


def detect_all(project_root):
    """Run all detection phases and return structured results."""
    project_root = os.path.abspath(os.path.expanduser(project_root))

    if not os.path.isdir(project_root):
        return {"error": f"Not a directory: {project_root}"}

    result = {
        "project_root": project_root,
        "languages": detect_languages(project_root),
        "frameworks": detect_frameworks(project_root),
        "package_managers": detect_package_manager(project_root),
        "cicd": detect_cicd(project_root),
        "build_tools": detect_build_tools(project_root),
        "services": detect_services(project_root),
        "claude_config": detect_claude_config(project_root),
    }

    # Derive primary language
    if result["languages"]:
        result["primary_language"] = result["languages"][0]["language"]
    else:
        result["primary_language"] = "Unknown"

    return result


def main():
    parser = argparse.ArgumentParser(description="Detect project technology stack")
    parser.add_argument(
        "project_root", nargs="?", default=".",
        help="Project root directory (default: current directory)",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    result = detect_all(args.project_root)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if "error" in result:
            print(f"Error: {result['error']}")
            sys.exit(1)

        print(f"\n{'=' * 60}")
        print(f"PROJECT PROFILE: {result['project_root']}")
        print(f"{'=' * 60}")

        print(f"\n  Primary Language: {result['primary_language']}")

        if result["languages"]:
            print(f"\n  Languages:")
            for lang in result["languages"]:
                print(f"    - {lang['language']} (via {lang['indicator']})")

        if result["frameworks"]:
            print(f"\n  Frameworks:")
            for fw in result["frameworks"]:
                print(f"    - {fw['framework']} (via {fw['indicator']})")

        if result["package_managers"]:
            print(f"\n  Package Managers:")
            for pm in result["package_managers"]:
                print(f"    - {pm['manager']} (via {pm['indicator']})")

        if result["cicd"]:
            print(f"\n  CI/CD:")
            for ci in result["cicd"]:
                print(f"    - {ci['system']} (via {ci['indicator']})")

        if result["build_tools"]:
            print(f"\n  Build/Test Tools:")
            for bt in result["build_tools"]:
                print(f"    - {bt['tool']} (via {bt['indicator']})")

        if result["services"]:
            print(f"\n  External Services:")
            for svc in result["services"]:
                print(f"    - {svc['service']} (via {svc['indicator']}) -> MCP: {svc['mcp_suggestion']}")

        cc = result["claude_config"]
        print(f"\n  Claude Code Config:")
        print(f"    CLAUDE.md files: {len(cc['claude_md'])}")
        print(f"    Settings: {', '.join(cc['settings']) or 'none'}")
        print(f"    Commands: {len(cc['commands'])}")
        print(f"    Skills: {len(cc['skills'])}")
        print(f"    Agents: {len(cc['agents'])}")
        if cc["mcp_config"]:
            servers = cc["mcp_config"].get("servers", [])
            print(f"    MCP Servers: {len(servers)} ({', '.join(servers[:5])})")
        print(f"    Plugins: {len(cc['plugins'])}")


if __name__ == "__main__":
    main()
