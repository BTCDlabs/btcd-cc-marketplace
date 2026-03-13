#!/usr/bin/env python3
"""Count tokens, words, and lines in files for context optimization analysis.

Provides deterministic token estimation for CLAUDE.md files, skill descriptions,
memory files, and other markdown content. Replaces ad-hoc "count chars / 4" or
"words * 1.3" instructions in skill prompts.

Token estimation uses word count * 1.3 (industry standard approximation for
English text with code mixed in). For pure code, multiply by 1.5.
"""

import argparse
import json
import os
import sys


# Token estimation ratios
PROSE_RATIO = 1.3    # words -> tokens for English prose
CODE_RATIO = 1.5     # words -> tokens for code-heavy content
MIXED_RATIO = 1.4    # words -> tokens for mixed content

# Thresholds from context-optimizer SKILL.md
TOKEN_BANDS = {
    "excellent": (0, 500),
    "good": (500, 1500),
    "warning": (1500, 3000),
    "critical": (3000, float("inf")),
}

# Skill description thresholds
DESC_EXCELLENT_MAX = 50   # words
DESC_GOOD_MAX = 100       # words
DESC_WARNING_MAX = 150    # words


def count_file(filepath, content_type="mixed"):
    """Count lines, words, chars, and estimate tokens for a file.

    Args:
        filepath: Path to file
        content_type: "prose", "code", or "mixed" for token ratio selection

    Returns dict with metrics or None on error.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, IOError) as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
        return None

    return count_string(content, content_type=content_type, filepath=filepath)


def count_string(content, content_type="mixed", filepath=None):
    """Count metrics for a string of content."""
    lines = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
    words = len(content.split())
    chars = len(content)

    ratio = {"prose": PROSE_RATIO, "code": CODE_RATIO, "mixed": MIXED_RATIO}.get(
        content_type, MIXED_RATIO
    )
    tokens = int(words * ratio)

    # Determine band
    band = "excellent"
    for name, (lo, hi) in TOKEN_BANDS.items():
        if lo <= tokens < hi:
            band = name
            break

    result = {
        "lines": lines,
        "words": words,
        "chars": chars,
        "tokens_estimated": tokens,
        "band": band,
        "content_type": content_type,
    }
    if filepath:
        result["filepath"] = filepath

    return result


def count_description(description_text):
    """Analyze a skill description for word count and quality band.

    Returns dict with word_count and quality assessment.
    """
    words = len(description_text.split())

    if words <= DESC_EXCELLENT_MAX:
        quality = "excellent"
    elif words <= DESC_GOOD_MAX:
        quality = "good"
    elif words <= DESC_WARNING_MAX:
        quality = "warning"
    else:
        quality = "bloated"

    return {
        "word_count": words,
        "quality": quality,
        "over_limit": words > DESC_WARNING_MAX,
        "under_minimum": words < 20,
    }


def analyze_claude_md_files(project_root="."):
    """Find and analyze all CLAUDE.md files in the project and user config.

    Searches:
    - Project root and all subdirectories for CLAUDE.md
    - ~/.claude/ for any .md files (user-level config)

    Does NOT walk the entire home directory.

    Returns list of analysis results.
    """
    import glob as globmod

    project_root = os.path.abspath(os.path.expanduser(project_root))
    found = set()
    results = []

    # Project-level: recursively find all CLAUDE.md files
    for filepath in globmod.glob(os.path.join(project_root, "**", "CLAUDE.md"), recursive=True):
        filepath = os.path.abspath(filepath)
        if filepath not in found:
            found.add(filepath)
            metrics = count_file(filepath, content_type="prose")
            if metrics:
                results.append(metrics)

    # Also check for .claude.local.md variants in project root
    for variant in ["CLAUDE.md", ".claude.local.md", "CLAUDE.local.md"]:
        filepath = os.path.abspath(os.path.join(project_root, variant))
        if filepath not in found and os.path.isfile(filepath):
            found.add(filepath)
            metrics = count_file(filepath, content_type="prose")
            if metrics:
                results.append(metrics)

    # User-level: check ~/.claude/ directory (not recursive walk of ~)
    user_claude_dir = os.path.expanduser("~/.claude")
    if os.path.isdir(user_claude_dir):
        for fname in os.listdir(user_claude_dir):
            if fname.endswith(".md"):
                filepath = os.path.join(user_claude_dir, fname)
                if filepath not in found and os.path.isfile(filepath):
                    found.add(filepath)
                    metrics = count_file(filepath, content_type="prose")
                    if metrics:
                        results.append(metrics)

    return results


def main():
    parser = argparse.ArgumentParser(description="Count tokens/words/lines in files")
    parser.add_argument("paths", nargs="*", help="File paths to analyze")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--type", choices=["prose", "code", "mixed"], default="mixed",
        help="Content type for token ratio (default: mixed)"
    )
    parser.add_argument(
        "--claude-md", action="store_true",
        help="Find and analyze all CLAUDE.md files in current project"
    )
    parser.add_argument(
        "--description", metavar="TEXT",
        help="Analyze a skill description string for quality"
    )
    parser.add_argument(
        "--summary", action="store_true",
        help="Show summary totals across all files"
    )
    args = parser.parse_args()

    results = []

    if args.description:
        result = count_description(args.description)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Words: {result['word_count']}")
            print(f"Quality: {result['quality']}")
            if result["over_limit"]:
                print(f"WARNING: Over {DESC_WARNING_MAX} word limit")
            if result["under_minimum"]:
                print(f"WARNING: Under 20 word minimum")
        return

    if args.claude_md:
        results = analyze_claude_md_files(".")
    else:
        for path in args.paths:
            path = os.path.expanduser(path)
            if os.path.isfile(path):
                metrics = count_file(path, content_type=args.type)
                if metrics:
                    results.append(metrics)
            elif os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    for fname in files:
                        if fname.endswith(".md"):
                            filepath = os.path.join(root, fname)
                            metrics = count_file(filepath, content_type=args.type)
                            if metrics:
                                results.append(metrics)
            else:
                print(f"Warning: {path} not found", file=sys.stderr)

    if not results:
        print("No files found to analyze.", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            fp = r.get("filepath", "<stdin>")
            print(f"\n{fp}:")
            print(f"  Lines:           {r['lines']}")
            print(f"  Words:           {r['words']}")
            print(f"  Characters:      {r['chars']}")
            print(f"  Tokens (est):    {r['tokens_estimated']}")
            print(f"  Band:            {r['band']}")

    if args.summary and len(results) > 1:
        total_lines = sum(r["lines"] for r in results)
        total_words = sum(r["words"] for r in results)
        total_tokens = sum(r["tokens_estimated"] for r in results)
        print(f"\n--- Summary ---")
        print(f"  Files:           {len(results)}")
        print(f"  Total lines:     {total_lines}")
        print(f"  Total words:     {total_words}")
        print(f"  Total tokens:    {total_tokens}")


if __name__ == "__main__":
    main()
