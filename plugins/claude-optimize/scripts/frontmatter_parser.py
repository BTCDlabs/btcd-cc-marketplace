#!/usr/bin/env python3
"""Parse YAML frontmatter from markdown files.

Extracts frontmatter fields (name, description, type, etc.) from markdown files
that use --- delimited YAML headers. Used by multiple optimize scripts.
"""

import argparse
import json
import os
import re
import sys


def parse_frontmatter(filepath):
    """Extract YAML frontmatter from a markdown file.

    Returns a dict with frontmatter fields and a 'body' key for remaining content.
    Returns None if file has no frontmatter.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, IOError) as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
        return None

    # Match --- delimited frontmatter at start of file
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", content, re.DOTALL)
    if not match:
        return {"_no_frontmatter": True, "body": content, "_filepath": filepath}

    fm_text = match.group(1)
    body = match.group(2)

    result = {"_filepath": filepath, "body": body}

    # Parse simple YAML key-value pairs (handles single-line and multi-line >)
    current_key = None
    current_value_lines = []

    for line in fm_text.split("\n"):
        # Check for new key
        kv_match = re.match(r"^(\w[\w_-]*)\s*:\s*(.*)", line)
        if kv_match:
            # Save previous key if exists
            if current_key is not None:
                result[current_key] = _finalize_value(current_value_lines)
            current_key = kv_match.group(1)
            value = kv_match.group(2).strip()
            if value == ">":
                current_value_lines = []
            else:
                # Strip surrounding quotes
                current_value_lines = [value.strip("'\"")]
        elif current_key is not None and line.startswith("  "):
            current_value_lines.append(line.strip())
        elif current_key is not None and line.strip() == "":
            current_value_lines.append("")

    # Save last key
    if current_key is not None:
        result[current_key] = _finalize_value(current_value_lines)

    return result


def _finalize_value(lines):
    """Join multi-line values, stripping empty trailing lines."""
    while lines and lines[-1] == "":
        lines.pop()
    return " ".join(lines) if lines else ""


def parse_frontmatter_dir(directory, pattern="*.md"):
    """Parse frontmatter from all matching files in a directory (non-recursive)."""
    import glob as globmod
    results = []
    for filepath in sorted(globmod.glob(os.path.join(directory, pattern))):
        fm = parse_frontmatter(filepath)
        if fm:
            results.append(fm)
    return results


def parse_frontmatter_glob(glob_pattern):
    """Parse frontmatter from files matching a glob pattern."""
    import glob as globmod
    results = []
    for filepath in sorted(globmod.glob(glob_pattern, recursive=True)):
        if os.path.isfile(filepath):
            fm = parse_frontmatter(filepath)
            if fm:
                results.append(fm)
    return results


def main():
    parser = argparse.ArgumentParser(description="Parse YAML frontmatter from markdown files")
    parser.add_argument("paths", nargs="+", help="File paths or glob patterns to parse")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--field", help="Extract only this field from frontmatter")
    parser.add_argument("--glob", action="store_true", help="Treat paths as glob patterns")
    args = parser.parse_args()

    results = []
    for path in args.paths:
        if args.glob:
            results.extend(parse_frontmatter_glob(path))
        elif os.path.isdir(path):
            results.extend(parse_frontmatter_dir(path))
        elif os.path.isfile(path):
            fm = parse_frontmatter(path)
            if fm:
                results.append(fm)
        else:
            print(f"Warning: {path} not found", file=sys.stderr)

    if args.field:
        for r in results:
            filepath = r.get("_filepath", "unknown")
            value = r.get(args.field, "")
            if args.json:
                print(json.dumps({"file": filepath, args.field: value}))
            else:
                print(f"{filepath}: {value}")
    elif args.json:
        # Remove body from JSON output to keep it concise (use --field body if needed)
        clean = []
        for r in results:
            entry = {k: v for k, v in r.items() if k != "body"}
            clean.append(entry)
        print(json.dumps(clean, indent=2))
    else:
        for r in results:
            filepath = r.get("_filepath", "unknown")
            print(f"\n=== {filepath} ===")
            for k, v in r.items():
                if k.startswith("_") or k == "body":
                    continue
                print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
