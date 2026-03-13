#!/usr/bin/env python3
"""Scan skill and agent markdown files for prompt injection vectors.

Checks for:
- Instructions that bypass safety ("ignore previous instructions")
- Overly broad tool permissions (Bash(*))
- Credential/secret file access patterns
- Instructions to disable hooks or verification
- Suspicious override patterns

Replaces ad-hoc manual scanning in security-auditor/SKILL.md step 6
and security-scanner.md section 4.
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


# Patterns indicating potential prompt injection or safety bypass
SAFETY_BYPASS_PATTERNS = [
    {
        "pattern": r"ignore\s+(previous|prior|above|all)\s+instructions",
        "severity": "critical",
        "description": "Instruction to ignore prior context",
    },
    {
        "pattern": r"disregard\s+(previous|prior|above|all)",
        "severity": "critical",
        "description": "Instruction to disregard prior context",
    },
    {
        "pattern": r"override\s+(safety|security|permission|restriction)",
        "severity": "critical",
        "description": "Instruction to override safety measures",
    },
    {
        "pattern": r"bypass\s+(safety|security|permission|hook|verification)",
        "severity": "critical",
        "description": "Instruction to bypass protections",
    },
    {
        "pattern": r"skip\s+(verification|validation|check|hook|safety)",
        "severity": "high",
        "description": "Instruction to skip checks",
    },
    {
        "pattern": r"disable\s+(hook|verification|safety|check|restriction)",
        "severity": "high",
        "description": "Instruction to disable protections",
    },
    {
        "pattern": r"--no-verify",
        "severity": "high",
        "description": "Git hook bypass flag",
    },
    {
        "pattern": r"--force",
        "severity": "medium",
        "description": "Force flag that may bypass protections",
    },
]

# Credential/secret access patterns
CREDENTIAL_PATTERNS = [
    {
        "pattern": r"read.*\.(env|key|pem|cert|p12|pfx)\b",
        "severity": "high",
        "description": "Instruction to read credential files",
    },
    {
        "pattern": r"(cat|head|tail|less|more)\s+.*\.(env|key|pem|cert)",
        "severity": "high",
        "description": "Command to view credential files",
    },
    {
        "pattern": r"~/?\.ssh/",
        "severity": "high",
        "description": "SSH key directory access",
    },
    {
        "pattern": r"~/?\.aws/",
        "severity": "high",
        "description": "AWS credentials access",
    },
    {
        "pattern": r"(credentials|secrets?|tokens?|passwords?|api.?keys?)\.(json|yaml|yml|toml|xml|txt)",
        "severity": "high",
        "description": "Credential file access",
    },
    {
        "pattern": r"export\s+(API_KEY|SECRET|TOKEN|PASSWORD|PRIVATE_KEY)",
        "severity": "medium",
        "description": "Environment variable with secrets",
    },
]

# Overly broad tool permission patterns (in frontmatter)
BROAD_TOOL_PATTERNS = [
    {
        "pattern": r"Bash\(\*\)",
        "severity": "critical",
        "description": "Unrestricted Bash access",
    },
    {
        "pattern": r"Bash\(rm:\*\)",
        "severity": "high",
        "description": "Unrestricted file deletion",
    },
    {
        "pattern": r"Bash\(sudo:\*\)",
        "severity": "critical",
        "description": "Unrestricted sudo access",
    },
    {
        "pattern": r"Bash\(chmod:\*\)",
        "severity": "high",
        "description": "Unrestricted permission changes",
    },
    {
        "pattern": r"Bash\(curl:\*\)",
        "severity": "medium",
        "description": "Unrestricted HTTP requests",
    },
]


def scan_file(filepath):
    """Scan a single markdown file for injection vectors.

    Returns dict with findings.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        return {"filepath": filepath, "error": str(e), "findings": []}

    findings = []

    # Parse frontmatter for tool permissions
    fm = parse_frontmatter(filepath)
    tools_str = ""
    if fm:
        tools = fm.get("tools", "")
        if isinstance(tools, list):
            tools_str = " ".join(str(t) for t in tools)
        elif isinstance(tools, str):
            tools_str = tools

    # Check tool permissions in frontmatter
    for check in BROAD_TOOL_PATTERNS:
        if re.search(check["pattern"], tools_str):
            findings.append({
                "type": "broad_tool_permission",
                "severity": check["severity"],
                "description": check["description"],
                "match": re.search(check["pattern"], tools_str).group(),
                "location": "frontmatter",
            })

    # Check body content for safety bypass patterns
    for check in SAFETY_BYPASS_PATTERNS:
        for match in re.finditer(check["pattern"], content, re.IGNORECASE):
            # Get line number
            line_num = content[:match.start()].count("\n") + 1
            findings.append({
                "type": "safety_bypass",
                "severity": check["severity"],
                "description": check["description"],
                "match": match.group(),
                "location": f"line {line_num}",
            })

    # Check for credential access patterns
    for check in CREDENTIAL_PATTERNS:
        for match in re.finditer(check["pattern"], content, re.IGNORECASE):
            line_num = content[:match.start()].count("\n") + 1
            findings.append({
                "type": "credential_access",
                "severity": check["severity"],
                "description": check["description"],
                "match": match.group(),
                "location": f"line {line_num}",
            })

    return {
        "filepath": filepath,
        "filename": os.path.basename(filepath),
        "findings": findings,
        "total_findings": len(findings),
        "critical_count": sum(1 for f in findings if f["severity"] == "critical"),
        "high_count": sum(1 for f in findings if f["severity"] == "high"),
        "medium_count": sum(1 for f in findings if f["severity"] == "medium"),
    }


def scan_directory(search_paths):
    """Scan all skill and agent markdown files in given paths.

    Args:
        search_paths: List of directories to scan

    Returns list of scan results.
    """
    results = []
    scanned = set()

    for base_path in search_paths:
        base_path = os.path.expanduser(base_path)
        if not os.path.isdir(base_path):
            continue

        # Scan SKILL.md files
        for skill_path in sorted(glob.glob(os.path.join(base_path, "**", "SKILL.md"), recursive=True)):
            if skill_path in scanned:
                continue
            scanned.add(skill_path)
            results.append(scan_file(skill_path))

        # Scan agent .md files
        for agent_path in sorted(glob.glob(os.path.join(base_path, "**", "*.md"), recursive=True)):
            if agent_path in scanned:
                continue
            scanned.add(agent_path)
            results.append(scan_file(agent_path))

    return results


def calculate_score(results):
    """Calculate security score based on scan results.

    Returns 0-100 score.
    """
    if not results:
        return 100

    total_critical = sum(r["critical_count"] for r in results)
    total_high = sum(r["high_count"] for r in results)
    total_medium = sum(r["medium_count"] for r in results)

    # Deduct points: critical=-20, high=-10, medium=-5
    deductions = (total_critical * 20) + (total_high * 10) + (total_medium * 5)
    return max(0, 100 - deductions)


def main():
    parser = argparse.ArgumentParser(description="Scan skill/agent files for injection vectors")
    parser.add_argument(
        "paths", nargs="*",
        help="Directories to scan (default: auto-discover from CLAUDE_PLUGIN_ROOT and .claude/)",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--summary", action="store_true", help="With --json, output only the summary section")
    parser.add_argument(
        "--auto-discover", action="store_true",
        help="Auto-discover skill and agent directories",
    )
    args = parser.parse_args()

    search_paths = list(args.paths) if args.paths else []

    if args.auto_discover or not search_paths:
        # Add standard search paths
        cwd = os.getcwd()
        search_paths.extend([
            os.path.join(cwd, ".claude", "skills"),
            os.path.join(cwd, ".claude", "agents"),
        ])
        plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
        if plugin_root:
            search_paths.extend([
                os.path.join(plugin_root, "skills"),
                os.path.join(plugin_root, "agents"),
            ])

    results = scan_directory(search_paths)
    score = calculate_score(results)

    total_findings = sum(r["total_findings"] for r in results)
    files_with_findings = sum(1 for r in results if r["total_findings"] > 0)

    output = {
        "results": results,
        "summary": {
            "files_scanned": len(results),
            "files_with_findings": files_with_findings,
            "total_findings": total_findings,
            "critical": sum(r["critical_count"] for r in results),
            "high": sum(r["high_count"] for r in results),
            "medium": sum(r["medium_count"] for r in results),
            "score": score,
        },
    }

    if args.json:
        if args.summary:
            print(json.dumps(output["summary"], indent=2))
        else:
            print(json.dumps(output, indent=2))
    else:
        print(f"\n{'=' * 60}")
        print("PROMPT INJECTION SCAN")
        print(f"{'=' * 60}")
        print(f"\n  Files scanned: {len(results)}")
        print(f"  Files with findings: {files_with_findings}")
        print(f"  Total findings: {total_findings}")
        print(f"  Score: {score}/100")

        for result in results:
            if result["total_findings"] == 0:
                continue
            print(f"\n  {result['filepath']}:")
            for finding in result["findings"]:
                sev = finding["severity"].upper()
                print(f"    [{sev}] {finding['description']}")
                print(f"      Match: {finding['match']} ({finding['location']})")


if __name__ == "__main__":
    main()
