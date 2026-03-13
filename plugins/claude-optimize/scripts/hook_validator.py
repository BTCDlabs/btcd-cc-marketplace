#!/usr/bin/env python3
"""Validate hook scripts for common issues.

Performs static analysis on hook scripts to detect:
- Missing shebang lines
- Missing set -euo pipefail
- Unquoted variables (injection risk)
- Missing executable permissions
- References to non-existent files
- Syntax errors (via bash -n)

Replaces ad-hoc code generation instructions in hook-recommender/SKILL.md
and security-scanner.md agent.
"""

import argparse
import json
import os
import re
import subprocess
import sys


class HookIssue:
    """Represents a single issue found in a hook script."""

    SEVERITY_CRITICAL = "critical"
    SEVERITY_HIGH = "high"
    SEVERITY_MEDIUM = "medium"
    SEVERITY_LOW = "low"

    def __init__(self, filepath, line_num, severity, category, message):
        self.filepath = filepath
        self.line_num = line_num
        self.severity = severity
        self.category = category
        self.message = message

    def to_dict(self):
        return {
            "file": self.filepath,
            "line": self.line_num,
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
        }


def check_shebang(filepath, lines):
    """Check for proper shebang line."""
    issues = []
    if not lines:
        issues.append(HookIssue(
            filepath, 1, HookIssue.SEVERITY_HIGH, "shebang",
            "Empty script file"
        ))
        return issues

    first_line = lines[0].strip()
    if not first_line.startswith("#!"):
        issues.append(HookIssue(
            filepath, 1, HookIssue.SEVERITY_HIGH, "shebang",
            f"Missing shebang line (first line: '{first_line[:50]}')"
        ))
    elif "bash" not in first_line and "sh" not in first_line and "python" not in first_line:
        issues.append(HookIssue(
            filepath, 1, HookIssue.SEVERITY_MEDIUM, "shebang",
            f"Unusual shebang: '{first_line}'"
        ))

    return issues


def check_strict_mode(filepath, lines, content):
    """Check for set -euo pipefail in bash scripts."""
    issues = []

    # Only check bash scripts
    if not lines or ("bash" not in lines[0] and "sh" not in lines[0]):
        return issues

    if "set -euo pipefail" not in content and "set -e" not in content:
        issues.append(HookIssue(
            filepath, 0, HookIssue.SEVERITY_MEDIUM, "strict_mode",
            "Missing 'set -euo pipefail' or 'set -e' (script may continue after errors)"
        ))

    return issues


def check_unquoted_variables(filepath, lines):
    """Check for unquoted variable expansions (injection risk)."""
    issues = []

    # Pattern: $VAR or ${VAR} not inside double quotes
    # This is a heuristic - we look for common dangerous patterns
    dangerous_contexts = [
        # Variable used in command position or argument without quotes
        re.compile(r'(?<!")\$\{?\w+\}?(?!")'),
    ]

    # Safer pattern: look for variables in specific dangerous contexts
    dangerous_patterns = [
        # Variable in if/test without quotes
        (re.compile(r'\[\s+\$\w+\s'), "unquoted variable in test expression"),
        # Variable in command argument without quotes
        (re.compile(r'(?:rm|mv|cp|cat|chmod|chown)\s+\$\w+'), "unquoted variable in file operation"),
        # Variable interpolation in eval
        (re.compile(r'eval\s+.*\$\w+'), "variable in eval (dangerous)"),
    ]

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Skip comments
        if stripped.startswith("#"):
            continue

        for pattern, desc in dangerous_patterns:
            if pattern.search(stripped):
                issues.append(HookIssue(
                    filepath, i, HookIssue.SEVERITY_HIGH, "injection_risk",
                    f"{desc}: {stripped[:80]}"
                ))

    return issues


def check_file_permissions(filepath):
    """Check if script has executable permissions."""
    issues = []
    if not os.access(filepath, os.X_OK):
        issues.append(HookIssue(
            filepath, 0, HookIssue.SEVERITY_MEDIUM, "permissions",
            "Script is not executable (missing +x permission)"
        ))
    return issues


def check_file_references(filepath, lines):
    """Check for references to non-existent files in the script."""
    issues = []

    # Look for file path patterns
    path_patterns = [
        re.compile(r'source\s+"?([^";\s]+)"?'),
        re.compile(r'\.\s+"?([^";\s]+)"?'),  # . sourcing
        re.compile(r'(?:cat|read|head|tail)\s+"?(/[^";\s]+)"?'),
    ]

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue

        for pattern in path_patterns:
            match = pattern.search(stripped)
            if match:
                ref_path = match.group(1)
                # Skip variable references and relative paths
                if "$" in ref_path or not ref_path.startswith("/"):
                    continue
                ref_path = os.path.expanduser(ref_path)
                if not os.path.exists(ref_path):
                    issues.append(HookIssue(
                        filepath, i, HookIssue.SEVERITY_LOW, "missing_file",
                        f"Referenced file not found: {ref_path}"
                    ))

    return issues


def check_syntax(filepath, lines):
    """Run bash -n syntax check on bash scripts."""
    issues = []

    if not lines or "bash" not in lines[0]:
        return issues

    try:
        result = subprocess.run(
            ["bash", "-n", filepath],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            error_text = result.stderr.strip()
            # Parse line numbers from bash error output
            for error_line in error_text.split("\n"):
                line_match = re.search(r"line (\d+)", error_line)
                line_num = int(line_match.group(1)) if line_match else 0
                issues.append(HookIssue(
                    filepath, line_num, HookIssue.SEVERITY_CRITICAL, "syntax",
                    f"Syntax error: {error_line.strip()}"
                ))
    except subprocess.TimeoutExpired:
        issues.append(HookIssue(
            filepath, 0, HookIssue.SEVERITY_MEDIUM, "syntax",
            "Syntax check timed out after 5 seconds"
        ))
    except FileNotFoundError:
        pass  # bash not available

    return issues


def check_input_handling(filepath, lines, content):
    """Check if script properly handles stdin (important for hooks that receive JSON)."""
    issues = []

    # Hook scripts should read from stdin if they process hook input
    # Check if script uses read/stdin patterns
    has_stdin_read = any(pattern in content for pattern in [
        "read ", "/dev/stdin", "cat -", "<&0", "sys.stdin",
    ])

    # If the script outputs JSON decisions, it likely needs to read stdin
    has_json_output = "decision" in content and ("block" in content or "allow" in content)

    if has_json_output and not has_stdin_read:
        issues.append(HookIssue(
            filepath, 0, HookIssue.SEVERITY_LOW, "input_handling",
            "Script produces hook decisions but may not read stdin input"
        ))

    return issues


def validate_hook_script(filepath):
    """Run all validation checks on a hook script.

    Returns list of HookIssue objects.
    """
    issues = []

    if not os.path.isfile(filepath):
        return [HookIssue(filepath, 0, HookIssue.SEVERITY_CRITICAL, "missing",
                          "Script file does not exist")]

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.split("\n")
    except (OSError, IOError) as e:
        return [HookIssue(filepath, 0, HookIssue.SEVERITY_CRITICAL, "read_error",
                          f"Cannot read script: {e}")]

    issues.extend(check_shebang(filepath, lines))
    issues.extend(check_strict_mode(filepath, lines, content))
    issues.extend(check_unquoted_variables(filepath, lines))
    issues.extend(check_file_permissions(filepath))
    issues.extend(check_file_references(filepath, lines))
    issues.extend(check_syntax(filepath, lines))
    issues.extend(check_input_handling(filepath, lines, content))

    return issues


def validate_hooks_from_config(settings_path):
    """Find all hook scripts referenced in a settings.json and validate them.

    Returns dict mapping script paths to their issues.
    """
    results = {}

    settings_path = os.path.expanduser(settings_path)
    if not os.path.isfile(settings_path):
        return results

    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except (json.JSONDecodeError, OSError):
        return results

    hook_config = settings.get("hooks", {})
    if not isinstance(hook_config, dict):
        return results

    for event_type, event_hooks in hook_config.items():
        if not isinstance(event_hooks, list):
            continue
        for hook_entry in event_hooks:
            if not isinstance(hook_entry, dict):
                continue
            for hook in hook_entry.get("hooks", []):
                if not isinstance(hook, dict):
                    continue
                command = hook.get("command", "")
                # Extract script path from command
                # Common patterns: "path/script.sh", "bash path/script.sh", etc.
                script_path = _extract_script_path(command)
                if script_path and script_path not in results:
                    results[script_path] = validate_hook_script(script_path)

    return results


def _extract_script_path(command):
    """Extract the script file path from a hook command string."""
    if not command:
        return None

    # Try to find a .sh or .py file path in the command
    parts = command.split()
    for part in parts:
        cleaned = part.strip("'\"")
        if cleaned.endswith((".sh", ".py", ".bash")):
            return os.path.expanduser(cleaned)

    return None


def main():
    parser = argparse.ArgumentParser(description="Validate hook scripts for common issues")
    parser.add_argument("scripts", nargs="*", help="Script file paths to validate")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--settings", metavar="PATH",
        help="Validate all hooks referenced in a settings.json file"
    )
    parser.add_argument(
        "--hooks-dir", metavar="DIR",
        help="Validate all scripts in a hooks directory"
    )
    args = parser.parse_args()

    all_issues = {}

    if args.settings:
        all_issues.update(validate_hooks_from_config(args.settings))
        # Also auto-scan the .claude/hooks/ directory adjacent to settings.json
        settings_dir = os.path.dirname(os.path.abspath(os.path.expanduser(args.settings)))
        hooks_dir = os.path.join(settings_dir, "hooks")
        if os.path.isdir(hooks_dir):
            for root, dirs, files in os.walk(hooks_dir):
                for fname in files:
                    if fname.endswith((".sh", ".py", ".bash")):
                        fpath = os.path.join(root, fname)
                        if fpath not in all_issues:
                            all_issues[fpath] = validate_hook_script(fpath)

    if args.hooks_dir:
        hooks_dir = os.path.expanduser(args.hooks_dir)
        if os.path.isdir(hooks_dir):
            for root, dirs, files in os.walk(hooks_dir):
                for fname in files:
                    if fname.endswith((".sh", ".py", ".bash")):
                        fpath = os.path.join(root, fname)
                        if fpath not in all_issues:
                            all_issues[fpath] = validate_hook_script(fpath)

    for script in args.scripts:
        script = os.path.expanduser(script)
        all_issues[script] = validate_hook_script(script)

    if not all_issues:
        print("No scripts found to validate.", file=sys.stderr)
        sys.exit(1)

    total_issues = sum(len(issues) for issues in all_issues.values())

    if args.json:
        output = {}
        for script, issues in all_issues.items():
            output[script] = [i.to_dict() for i in issues]
        output["_summary"] = {
            "scripts_checked": len(all_issues),
            "total_issues": total_issues,
            "critical": sum(1 for issues in all_issues.values()
                          for i in issues if i.severity == "critical"),
            "high": sum(1 for issues in all_issues.values()
                       for i in issues if i.severity == "high"),
            "medium": sum(1 for issues in all_issues.values()
                         for i in issues if i.severity == "medium"),
            "low": sum(1 for issues in all_issues.values()
                      for i in issues if i.severity == "low"),
        }
        print(json.dumps(output, indent=2))
    else:
        for script, issues in all_issues.items():
            status = "PASS" if not issues else "FAIL"
            print(f"\n{'=' * 60}")
            print(f"[{status}] {script}")
            print(f"{'=' * 60}")
            if not issues:
                print("  No issues found.")
            else:
                for issue in sorted(issues, key=lambda i: (
                    {"critical": 0, "high": 1, "medium": 2, "low": 3}[i.severity],
                    i.line_num
                )):
                    line_str = f"L{issue.line_num}" if issue.line_num else "   "
                    print(f"  [{issue.severity.upper():8s}] {line_str:>5s} [{issue.category}] {issue.message}")

        print(f"\n--- Summary ---")
        print(f"Scripts checked: {len(all_issues)}")
        print(f"Total issues: {total_issues}")
        passed = sum(1 for issues in all_issues.values() if not issues)
        print(f"Passed: {passed}/{len(all_issues)}")


if __name__ == "__main__":
    main()
