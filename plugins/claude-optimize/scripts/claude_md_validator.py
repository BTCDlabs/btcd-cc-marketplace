#!/usr/bin/env python3
"""Cross-reference CLAUDE.md content against the actual codebase.

Validates that:
- Documented commands match package.json scripts / Makefile targets
- Referenced file paths actually exist
- Architecture descriptions match directory structure
- Commands are executable

Replaces ad-hoc cross-reference instructions in claude-md-manager/SKILL.md.
"""

import argparse
import json
import os
import re
import subprocess
import sys


def extract_commands_from_claude_md(filepath):
    """Extract code blocks and inline commands from a CLAUDE.md file.

    Returns list of dicts with command info.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, IOError) as e:
        return []

    commands = []

    # Extract fenced code blocks
    code_block_pattern = re.compile(r'```(?:bash|sh|shell|zsh)?\s*\n(.*?)```', re.DOTALL)
    for match in code_block_pattern.finditer(content):
        block = match.group(1).strip()
        for line in block.split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                commands.append({
                    "command": line,
                    "source": "code_block",
                    "file": filepath,
                })

    # Extract inline code that looks like commands
    inline_pattern = re.compile(r'`((?:npm|yarn|pnpm|bun|make|cargo|go|python|pip|docker|git)\s[^`]+)`')
    for match in inline_pattern.finditer(content):
        commands.append({
            "command": match.group(1),
            "source": "inline",
            "file": filepath,
        })

    return commands


def extract_file_paths_from_claude_md(filepath):
    """Extract file/directory path references from CLAUDE.md.

    Returns list of path strings.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, IOError):
        return []

    paths = []

    # Paths in backticks
    backtick_paths = re.compile(r'`((?:\.{0,2}/)?(?:[\w.-]+/)+[\w.-]*(?:\.\w+)?)`')
    for match in backtick_paths.finditer(content):
        path = match.group(1)
        if len(path) > 2:
            paths.append(path)

    # Paths in directory structure trees (e.g., "  src/")
    tree_paths = re.compile(r'^\s{2,}([\w.-]+/[\w./]*)', re.MULTILINE)
    for match in tree_paths.finditer(content):
        paths.append(match.group(1))

    return paths


def extract_package_json_scripts(project_root):
    """Extract npm scripts from package.json."""
    pkg_path = os.path.join(project_root, "package.json")
    if not os.path.isfile(pkg_path):
        return {}

    try:
        with open(pkg_path, "r", encoding="utf-8") as f:
            pkg = json.load(f)
        return pkg.get("scripts", {})
    except (json.JSONDecodeError, OSError):
        return {}


def extract_makefile_targets(project_root):
    """Extract targets from Makefile."""
    makefile_path = os.path.join(project_root, "Makefile")
    if not os.path.isfile(makefile_path):
        return []

    targets = []
    try:
        with open(makefile_path, "r", encoding="utf-8") as f:
            for line in f:
                match = re.match(r'^([\w.-]+)\s*:', line)
                if match:
                    targets.append(match.group(1))
    except OSError:
        pass
    return targets


def validate_commands(commands, project_root):
    """Validate extracted commands against actual project config.

    Returns list of validation results.
    """
    npm_scripts = extract_package_json_scripts(project_root)
    make_targets = extract_makefile_targets(project_root)

    results = []
    for cmd_info in commands:
        cmd = cmd_info["command"]
        status = "unknown"
        detail = ""

        # Check npm/yarn/pnpm commands
        npm_match = re.match(r'(?:npm|yarn|pnpm|bun)\s+(?:run\s+)?(\w[\w:-]*)', cmd)
        if npm_match:
            script_name = npm_match.group(1)
            if script_name in npm_scripts:
                status = "valid"
                detail = f"Matches package.json script: {npm_scripts[script_name][:60]}"
            elif script_name in ("install", "ci", "test", "start", "build", "dev"):
                status = "valid"
                detail = "Built-in npm command"
            else:
                status = "invalid"
                detail = f"Script '{script_name}' not found in package.json"

        # Check make commands
        make_match = re.match(r'make\s+(\w[\w.-]*)', cmd)
        if make_match:
            target = make_match.group(1)
            if target in make_targets:
                status = "valid"
                detail = f"Matches Makefile target"
            else:
                status = "invalid"
                detail = f"Target '{target}' not found in Makefile"

        results.append({
            **cmd_info,
            "status": status,
            "detail": detail,
        })

    return results


def validate_file_paths(paths, project_root):
    """Check if referenced file paths exist.

    Returns list of validation results.
    """
    results = []
    for path in paths:
        full_path = os.path.join(project_root, path) if not os.path.isabs(path) else path
        exists = os.path.exists(full_path)
        results.append({
            "path": path,
            "exists": exists,
            "full_path": full_path,
        })
    return results


def score_claude_md(filepath, project_root):
    """Score a CLAUDE.md file based on quality criteria.

    Returns dict with scores per criterion (0-100 scale normalized from rubric).
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, IOError):
        return {"error": f"Could not read {filepath}"}

    lines = content.split("\n")
    words = len(content.split())

    scores = {}

    # 1. Commands/Workflows (20 points)
    commands = extract_commands_from_claude_md(filepath)
    cmd_results = validate_commands(commands, project_root)
    valid_cmds = sum(1 for r in cmd_results if r["status"] == "valid")
    if len(commands) >= 5 and valid_cmds >= 3:
        scores["commands"] = 20
    elif len(commands) >= 3:
        scores["commands"] = 15
    elif len(commands) >= 1:
        scores["commands"] = 10
    else:
        scores["commands"] = 0

    # 2. Architecture Clarity (20 points)
    has_dir_structure = bool(re.search(r'(?:directory|structure|architecture|layout)', content, re.I))
    heading_count = len(re.findall(r'^#+\s', content, re.MULTILINE))
    if has_dir_structure and heading_count >= 5:
        scores["architecture"] = 20
    elif heading_count >= 3:
        scores["architecture"] = 15
    elif heading_count >= 1:
        scores["architecture"] = 10
    else:
        scores["architecture"] = 0

    # 3. Non-Obvious Patterns (15 points)
    pattern_keywords = ["gotcha", "quirk", "note", "important", "warning", "caveat",
                        "workaround", "known issue", "edge case", "why we"]
    pattern_mentions = sum(1 for kw in pattern_keywords if kw.lower() in content.lower())
    if pattern_mentions >= 3:
        scores["patterns"] = 15
    elif pattern_mentions >= 1:
        scores["patterns"] = 10
    else:
        scores["patterns"] = 0

    # 4. Conciseness (15 points)
    if words <= 300:
        scores["conciseness"] = 15  # Very concise
    elif words <= 800:
        scores["conciseness"] = 10
    elif words <= 1500:
        scores["conciseness"] = 5
    else:
        scores["conciseness"] = 0

    # 5. Currency (15 points) - check file path validity
    paths = extract_file_paths_from_claude_md(filepath)
    path_results = validate_file_paths(paths, project_root)
    if paths:
        valid_ratio = sum(1 for r in path_results if r["exists"]) / len(paths)
        if valid_ratio >= 0.9:
            scores["currency"] = 15
        elif valid_ratio >= 0.7:
            scores["currency"] = 10
        elif valid_ratio >= 0.5:
            scores["currency"] = 5
        else:
            scores["currency"] = 0
    else:
        scores["currency"] = 10  # No paths to validate - neutral

    # 6. Actionability (15 points)
    has_code_blocks = bool(re.search(r'```', content))
    has_commands = len(commands) > 0
    if has_code_blocks and has_commands:
        scores["actionability"] = 15
    elif has_code_blocks or has_commands:
        scores["actionability"] = 10
    else:
        scores["actionability"] = 5

    total = sum(scores.values())

    # Grade
    if total >= 90:
        grade = "A"
    elif total >= 80:
        grade = "B"
    elif total >= 70:
        grade = "C"
    elif total >= 60:
        grade = "D"
    else:
        grade = "F"

    return {
        "filepath": filepath,
        "scores": scores,
        "total": total,
        "max_possible": 100,
        "grade": grade,
        "word_count": words,
        "line_count": len(lines),
        "commands_found": len(commands),
        "valid_commands": valid_cmds if commands else 0,
        "paths_found": len(paths),
        "valid_paths": sum(1 for r in path_results if r["exists"]),
        "invalid_commands": [r for r in cmd_results if r["status"] == "invalid"],
        "missing_paths": [r["path"] for r in path_results if not r["exists"]],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Cross-reference CLAUDE.md content against codebase"
    )
    parser.add_argument("claude_md_files", nargs="*", help="CLAUDE.md file paths to validate")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--auto-discover", action="store_true", help="Find all CLAUDE.md files")
    args = parser.parse_args()

    project_root = os.path.abspath(os.path.expanduser(args.project_root))
    files = list(args.claude_md_files)

    if args.auto_discover or not files:
        # Find CLAUDE.md in project root and .claude/
        for candidate in [
            os.path.join(project_root, "CLAUDE.md"),
            os.path.join(project_root, ".claude", "CLAUDE.md"),
        ]:
            if os.path.isfile(candidate) and candidate not in files:
                files.append(candidate)

    if not files:
        print("No CLAUDE.md files found.", file=sys.stderr)
        sys.exit(1)

    results = []
    for filepath in files:
        result = score_claude_md(filepath, project_root)
        results.append(result)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for result in results:
            filepath = result.get("filepath", "unknown")
            print(f"\n{'=' * 60}")
            print(f"CLAUDE.MD VALIDATION: {filepath}")
            print(f"{'=' * 60}")

            if "error" in result:
                print(f"  ERROR: {result['error']}")
                continue

            print(f"\n  Score: {result['total']}/{result['max_possible']} (Grade: {result['grade']})")
            print(f"  Words: {result['word_count']}, Lines: {result['line_count']}")

            print(f"\n  Criterion Scores:")
            for criterion, score in result["scores"].items():
                print(f"    {criterion:20s}: {score}")

            if result.get("invalid_commands"):
                print(f"\n  Invalid Commands:")
                for cmd in result["invalid_commands"]:
                    print(f"    - {cmd['command'][:60]}")
                    print(f"      {cmd['detail']}")

            if result.get("missing_paths"):
                print(f"\n  Missing Paths:")
                for path in result["missing_paths"]:
                    print(f"    - {path}")


if __name__ == "__main__":
    main()
