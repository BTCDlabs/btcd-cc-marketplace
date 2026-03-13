#!/usr/bin/env python3
"""Audit Claude Code permission rules (allow/deny) from settings.json.

Parses allow and deny rules, flags overly broad permissions, checks for missing
critical deny rules, and generates a security posture score. Replaces ad-hoc
JSON parsing and pattern matching in security-scanner.md and security-auditor SKILL.md.
"""

import argparse
import json
import os
import re
import sys


# Critical deny rules that should always be present
CRITICAL_DENY_RULES = [
    {"pattern": "rm -rf /", "prevents": "Root filesystem deletion"},
    {"pattern": "rm -rf ~", "prevents": "Home directory deletion"},
    {"pattern": "chmod 777", "prevents": "World-writable permissions"},
    {"pattern": "git push --force origin main", "prevents": "Force push to main"},
    {"pattern": "git push --force origin master", "prevents": "Force push to master"},
]

# High priority deny rules
HIGH_PRIORITY_DENY = [
    {"pattern": "curl|sh", "prevents": "Pipe-to-shell attacks"},
    {"pattern": "curl|bash", "prevents": "Pipe-to-shell attacks"},
    {"pattern": "wget|sh", "prevents": "Pipe-to-shell attacks"},
    {"pattern": "wget|bash", "prevents": "Pipe-to-shell attacks"},
    {"pattern": "DROP TABLE", "prevents": "Database table destruction"},
    {"pattern": "TRUNCATE TABLE", "prevents": "Table data destruction"},
]

# Overly broad allow patterns that are dangerous
DANGEROUS_ALLOW_PATTERNS = {
    "Bash(*)": {"risk": "critical", "why": "Allows any bash command"},
    "Bash(rm:*)": {"risk": "high", "why": "Allows any file deletion"},
    "Bash(sudo:*)": {"risk": "critical", "why": "Allows privilege escalation"},
    "Bash(curl:*)": {"risk": "medium", "why": "Allows arbitrary HTTP requests"},
    "Bash(chmod:*)": {"risk": "high", "why": "Allows permission changes"},
    "Bash(chown:*)": {"risk": "high", "why": "Allows ownership changes"},
}

# Safe allow patterns for reference
SAFE_ALLOW_PATTERNS = [
    "Bash(git:*)", "Bash(npm:*)", "Bash(yarn:*)", "Bash(pnpm:*)",
    "Bash(node:*)", "Bash(python3:*)", "Bash(cargo:*)", "Bash(make:*)",
    "Bash(docker:*)", "Bash(gh:*)", "Bash(jq:*)",
    "Bash(wc:*)", "Bash(sort:*)", "Bash(head:*)", "Bash(tail:*)",
]

# Sensitive file patterns to check in deny rules
SENSITIVE_FILE_PATTERNS = [
    ".env", "*.key", "*.pem", "*credentials*", "*secret*",
    "~/.ssh/*", "~/.aws/*",
]


def load_settings(settings_path):
    """Load and return settings from a settings.json file."""
    settings_path = os.path.expanduser(settings_path)
    if not os.path.isfile(settings_path):
        return None

    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error reading {settings_path}: {e}", file=sys.stderr)
        return None


def audit_deny_rules(settings):
    """Audit deny rules for completeness.

    Returns dict with findings.
    """
    deny_rules = settings.get("deny", [])
    if not isinstance(deny_rules, list):
        deny_rules = []

    deny_text = " ".join(str(r) for r in deny_rules).lower()

    findings = {
        "total_deny_rules": len(deny_rules),
        "rules": deny_rules,
        "missing_critical": [],
        "missing_high": [],
        "has_sensitive_file_protection": False,
    }

    # Check critical deny rules
    for rule in CRITICAL_DENY_RULES:
        if rule["pattern"].lower() not in deny_text:
            findings["missing_critical"].append(rule)

    # Check high priority deny rules
    for rule in HIGH_PRIORITY_DENY:
        if rule["pattern"].lower() not in deny_text:
            findings["missing_high"].append(rule)

    # Check for sensitive file protection
    sensitive_covered = 0
    for pattern in SENSITIVE_FILE_PATTERNS:
        if pattern.lower() in deny_text:
            sensitive_covered += 1
    findings["has_sensitive_file_protection"] = sensitive_covered > 0
    findings["sensitive_patterns_covered"] = sensitive_covered
    findings["sensitive_patterns_total"] = len(SENSITIVE_FILE_PATTERNS)

    return findings


def audit_allow_rules(settings):
    """Audit allow rules for overly broad permissions.

    Returns dict with findings.
    """
    allow_rules = settings.get("allow", [])
    if not isinstance(allow_rules, list):
        allow_rules = []

    findings = {
        "total_allow_rules": len(allow_rules),
        "rules": allow_rules,
        "dangerous": [],
        "safe": [],
        "custom": [],
    }

    for rule in allow_rules:
        rule_str = str(rule)
        if rule_str in DANGEROUS_ALLOW_PATTERNS:
            info = DANGEROUS_ALLOW_PATTERNS[rule_str]
            findings["dangerous"].append({
                "pattern": rule_str,
                "risk": info["risk"],
                "why": info["why"],
            })
        elif rule_str in SAFE_ALLOW_PATTERNS:
            findings["safe"].append(rule_str)
        else:
            findings["custom"].append(rule_str)

    return findings


def calculate_security_score(deny_findings, allow_findings):
    """Calculate a security posture score (0-100).

    Scoring breakdown:
    - Deny rules completeness: 0-40 points
    - Allow rules safety: 0-30 points
    - Sensitive file protection: 0-15 points
    - Overall configuration: 0-15 points
    """
    score = 0

    # Deny rules (40 points)
    total_critical = len(CRITICAL_DENY_RULES)
    missing_critical = len(deny_findings["missing_critical"])
    critical_coverage = (total_critical - missing_critical) / total_critical if total_critical > 0 else 0
    score += int(critical_coverage * 25)

    total_high = len(HIGH_PRIORITY_DENY)
    missing_high = len(deny_findings["missing_high"])
    high_coverage = (total_high - missing_high) / total_high if total_high > 0 else 0
    score += int(high_coverage * 15)

    # Allow rules (30 points)
    if not allow_findings["dangerous"]:
        score += 30
    else:
        critical_dangerous = sum(1 for d in allow_findings["dangerous"] if d["risk"] == "critical")
        high_dangerous = sum(1 for d in allow_findings["dangerous"] if d["risk"] == "high")
        if critical_dangerous == 0:
            score += 15
        if high_dangerous == 0:
            score += 10
        if len(allow_findings["dangerous"]) <= 1:
            score += 5

    # Sensitive file protection (15 points)
    if deny_findings["has_sensitive_file_protection"]:
        ratio = deny_findings["sensitive_patterns_covered"] / deny_findings["sensitive_patterns_total"]
        score += int(ratio * 15)

    # Overall configuration (15 points)
    if deny_findings["total_deny_rules"] > 0:
        score += 5
    if deny_findings["total_deny_rules"] >= 5:
        score += 5
    if allow_findings["total_allow_rules"] > 0:
        score += 5  # At least some explicit allow rules configured

    return min(score, 100)


def check_env_protection(settings):
    """Check if hooks exist to protect sensitive files from writes.

    Returns dict with protection status.
    """
    PROTECTED_PATTERNS = [".env", "*.key", "*.pem", "*.cert", "credentials.*", "secrets.*"]

    hooks = settings.get("hooks", {})
    protection_hooks = []

    for event_type in ["PreToolUse", "PostToolUse"]:
        event_hooks = hooks.get(event_type, [])
        if not isinstance(event_hooks, list):
            continue
        for hook_entry in event_hooks:
            if not isinstance(hook_entry, dict):
                continue
            matcher = hook_entry.get("matcher", "")
            if any(tool in matcher for tool in ["Write", "Edit"]):
                for hook in hook_entry.get("hooks", []):
                    cmd = hook.get("command", "") if isinstance(hook, dict) else ""
                    for pattern in PROTECTED_PATTERNS:
                        if pattern.replace("*", "") in cmd:
                            protection_hooks.append({
                                "event": event_type,
                                "matcher": matcher,
                                "protects": pattern,
                            })

    return {
        "has_protection": len(protection_hooks) > 0,
        "protection_hooks": protection_hooks,
        "recommended_patterns": PROTECTED_PATTERNS,
    }


def check_precompact_hook(settings):
    """Check if a PreCompact hook exists for context preservation.

    Returns dict with hook status.
    """
    hooks = settings.get("hooks", {})
    precompact = hooks.get("PreCompact", [])

    return {
        "has_precompact_hook": isinstance(precompact, list) and len(precompact) > 0,
        "hook_count": len(precompact) if isinstance(precompact, list) else 0,
    }


def audit_settings(settings_path):
    """Run full permission audit on a settings file.

    Returns dict with all findings and score.
    """
    settings = load_settings(settings_path)
    if settings is None:
        return {
            "error": f"Could not load settings from {settings_path}",
            "score": 0,
            "grade": "F",
        }

    deny_findings = audit_deny_rules(settings)
    allow_findings = audit_allow_rules(settings)
    env_protection = check_env_protection(settings)
    precompact = check_precompact_hook(settings)
    score = calculate_security_score(deny_findings, allow_findings)

    # Assign grade
    if score >= 90:
        grade = "A"
    elif score >= 80:
        grade = "B"
    elif score >= 70:
        grade = "C"
    elif score >= 60:
        grade = "D"
    else:
        grade = "F"

    return {
        "settings_path": settings_path,
        "deny_rules": deny_findings,
        "allow_rules": allow_findings,
        "env_protection": env_protection,
        "precompact_hook": precompact,
        "score": score,
        "grade": grade,
    }


def main():
    parser = argparse.ArgumentParser(description="Audit Claude Code permission rules")
    parser.add_argument(
        "settings_paths", nargs="*",
        default=[".claude/settings.json", os.path.expanduser("~/.claude/settings.json")],
        help="Paths to settings.json files (default: project + user settings)",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    results = []
    for path in args.settings_paths:
        result = audit_settings(path)
        results.append(result)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for result in results:
            path = result.get("settings_path", "unknown")
            print(f"\n{'=' * 60}")
            print(f"PERMISSION AUDIT: {path}")
            print(f"{'=' * 60}")

            if "error" in result:
                print(f"  ERROR: {result['error']}")
                continue

            print(f"\n  Score: {result['score']}/100 (Grade: {result['grade']})")

            deny = result["deny_rules"]
            print(f"\n  Deny Rules ({deny['total_deny_rules']} configured):")
            if deny["missing_critical"]:
                print(f"    CRITICAL MISSING ({len(deny['missing_critical'])}):")
                for rule in deny["missing_critical"]:
                    print(f"      - {rule['pattern']} ({rule['prevents']})")
            else:
                print(f"    All critical deny rules present.")

            if deny["missing_high"]:
                print(f"    HIGH PRIORITY MISSING ({len(deny['missing_high'])}):")
                for rule in deny["missing_high"]:
                    print(f"      - {rule['pattern']} ({rule['prevents']})")

            allow = result["allow_rules"]
            print(f"\n  Allow Rules ({allow['total_allow_rules']} configured):")
            if allow["dangerous"]:
                print(f"    DANGEROUS ({len(allow['dangerous'])}):")
                for d in allow["dangerous"]:
                    print(f"      - {d['pattern']} [{d['risk']}] {d['why']}")
            else:
                print(f"    No dangerous allow patterns found.")

            if not deny["has_sensitive_file_protection"]:
                print(f"\n  WARNING: No sensitive file protection in deny rules")


if __name__ == "__main__":
    main()
