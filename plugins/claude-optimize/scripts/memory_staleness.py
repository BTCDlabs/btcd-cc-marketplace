#!/usr/bin/env python3
"""Detect stale entries in Claude Code memory files.

Checks if file paths, function names, and package names referenced in memory
entries still exist in the codebase. Replaces ad-hoc grep-based staleness
detection in memory-manager/SKILL.md.
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys

# Add scripts dir to path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frontmatter_parser import parse_frontmatter


def extract_references(content):
    """Extract file paths, function names, and package names from text.

    Returns dict with lists of each type of reference found.
    """
    refs = {
        "file_paths": [],
        "identifiers": [],
        "packages": [],
    }

    # File paths (absolute and relative)
    # Match paths like /foo/bar.py, src/utils.ts, ./config.json
    path_pattern = re.compile(
        r'(?:^|\s|[`"\'])((?:/[\w.-]+)+(?:\.\w+)?|(?:\.{0,2}/)?(?:[\w.-]+/)+[\w.-]+(?:\.\w+)?)'
    )
    for match in path_pattern.finditer(content):
        path = match.group(1).strip("`'\"")
        if len(path) > 3 and "/" in path:
            refs["file_paths"].append(path)

    # Package/module names (e.g., from npm, pip, cargo)
    # Look for patterns like "use <package>", "import <package>", "<package>@version"
    pkg_patterns = [
        re.compile(r'(?:npm|yarn|pnpm)\s+(?:install|add)\s+([\w@/-]+)'),
        re.compile(r'(?:pip|pip3)\s+install\s+([\w-]+)'),
        re.compile(r'import\s+([\w.]+)'),
        re.compile(r'from\s+([\w.]+)\s+import'),
        re.compile(r'require\(["\']([^"\']+)["\']\)'),
    ]
    for pattern in pkg_patterns:
        for match in pattern.finditer(content):
            refs["packages"].append(match.group(1))

    # Function/class names (identifiers in backticks)
    backtick_pattern = re.compile(r'`([\w.]+(?:\(\))?)`')
    for match in backtick_pattern.finditer(content):
        ident = match.group(1).rstrip("()")
        if len(ident) > 2 and not ident.startswith("/"):
            refs["identifiers"].append(ident)

    return refs


def check_file_exists(path, project_root):
    """Check if a file path exists relative to project root."""
    if os.path.isabs(path):
        return os.path.exists(path)
    return os.path.exists(os.path.join(project_root, path))


def search_codebase(pattern, project_root):
    """Search for a pattern in the codebase using grep.

    Returns True if found, False otherwise.
    """
    try:
        result = subprocess.run(
            ["grep", "-r", "-l", "--include=*.py", "--include=*.js", "--include=*.ts",
             "--include=*.go", "--include=*.rs", "--include=*.java",
             "--include=*.json", "--include=*.yaml", "--include=*.yml",
             "--include=*.toml", "--include=*.md",
             "-m", "1", pattern, project_root],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def analyze_memory_entry(entry_text, project_root):
    """Analyze a single memory entry for staleness.

    Returns dict with staleness analysis.
    """
    refs = extract_references(entry_text)

    total_refs = 0
    found_refs = 0
    missing_refs = []

    # Check file paths
    for path in refs["file_paths"]:
        total_refs += 1
        if check_file_exists(path, project_root):
            found_refs += 1
        else:
            missing_refs.append({"type": "file_path", "ref": path})

    # Check identifiers in codebase
    for ident in refs["identifiers"]:
        total_refs += 1
        if search_codebase(ident, project_root):
            found_refs += 1
        else:
            missing_refs.append({"type": "identifier", "ref": ident})

    # Calculate staleness score (0-25 per memory-manager SKILL.md)
    if total_refs == 0:
        staleness_score = 15  # No references to check - neutral
    else:
        ratio = found_refs / total_refs
        if ratio >= 0.9:
            staleness_score = 25  # Almost all references valid
        elif ratio >= 0.7:
            staleness_score = 15
        elif ratio >= 0.4:
            staleness_score = 5
        else:
            staleness_score = 0  # Most references invalid

    return {
        "total_references": total_refs,
        "found_references": found_refs,
        "missing_references": missing_refs,
        "staleness_score": staleness_score,
        "is_stale": staleness_score < 10,
    }


def analyze_memory_file(filepath, project_root):
    """Analyze a complete memory file for staleness.

    Returns dict with per-entry and aggregate analysis.
    """
    fm = parse_frontmatter(filepath)
    if fm is None:
        return {"error": f"Could not parse {filepath}"}

    body = fm.get("body", "")
    name = fm.get("name", os.path.basename(filepath))
    mem_type = fm.get("type", "unknown")

    # Split body into logical entries (by ## headers or double newlines)
    entries = []
    current_entry = []
    for line in body.split("\n"):
        if line.startswith("## ") and current_entry:
            entries.append("\n".join(current_entry))
            current_entry = [line]
        else:
            current_entry.append(line)
    if current_entry:
        entries.append("\n".join(current_entry))

    # If no clear sections, treat whole body as one entry
    if not entries:
        entries = [body]

    entry_results = []
    for i, entry_text in enumerate(entries):
        entry_text = entry_text.strip()
        if not entry_text:
            continue
        analysis = analyze_memory_entry(entry_text, project_root)
        analysis["entry_index"] = i
        analysis["entry_preview"] = entry_text[:100]
        entry_results.append(analysis)

    avg_score = (
        sum(e["staleness_score"] for e in entry_results) / len(entry_results)
        if entry_results else 0
    )

    return {
        "filepath": filepath,
        "name": name,
        "type": mem_type,
        "total_entries": len(entry_results),
        "stale_entries": sum(1 for e in entry_results if e["is_stale"]),
        "average_staleness_score": round(avg_score, 1),
        "entries": entry_results,
    }


def find_duplicates(memory_files_data):
    """Find duplicate and near-duplicate entries across memory files.

    Returns list of duplicate pairs.
    """
    duplicates = []
    all_entries = []

    for file_data in memory_files_data:
        if "entries" not in file_data:
            continue
        for entry in file_data["entries"]:
            preview = entry.get("entry_preview", "").strip().lower()
            if len(preview) > 20:
                all_entries.append({
                    "file": file_data["filepath"],
                    "index": entry["entry_index"],
                    "preview": preview,
                    "words": set(preview.split()),
                })

    # Compare all pairs for similarity
    for i in range(len(all_entries)):
        for j in range(i + 1, len(all_entries)):
            a = all_entries[i]
            b = all_entries[j]

            # Exact duplicate
            if a["preview"] == b["preview"]:
                duplicates.append({
                    "type": "exact",
                    "file_a": a["file"],
                    "file_b": b["file"],
                    "preview": a["preview"][:80],
                })
                continue

            # Jaccard similarity for near-duplicates
            if a["words"] and b["words"]:
                intersection = len(a["words"] & b["words"])
                union = len(a["words"] | b["words"])
                similarity = intersection / union if union > 0 else 0
                if similarity > 0.7:
                    duplicates.append({
                        "type": "near_duplicate",
                        "similarity": round(similarity, 2),
                        "file_a": a["file"],
                        "file_b": b["file"],
                        "preview_a": a["preview"][:60],
                        "preview_b": b["preview"][:60],
                    })

    return duplicates


def main():
    parser = argparse.ArgumentParser(
        description="Detect stale entries in Claude Code memory files"
    )
    parser.add_argument("memory_files", nargs="*", help="Memory file paths to analyze")
    parser.add_argument("--project-root", default=".", help="Project root for reference checking")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--memory-dir", metavar="DIR",
        help="Analyze all .md files in this memory directory"
    )
    parser.add_argument(
        "--check-duplicates", action="store_true",
        help="Also check for duplicate entries across files"
    )
    args = parser.parse_args()

    project_root = os.path.abspath(os.path.expanduser(args.project_root))
    files_to_check = list(args.memory_files)

    if args.memory_dir:
        mem_dir = os.path.expanduser(args.memory_dir)
        if os.path.isdir(mem_dir):
            files_to_check.extend(sorted(glob.glob(os.path.join(mem_dir, "*.md"))))

    if not files_to_check:
        # Auto-discover memory directory
        cwd = os.getcwd()
        encoded = cwd.replace("/", "-").lstrip("-")
        mem_dir = os.path.expanduser(f"~/.claude/projects/{encoded}/memory")
        if os.path.isdir(mem_dir):
            files_to_check = sorted(glob.glob(os.path.join(mem_dir, "*.md")))
        if not files_to_check:
            print("No memory files found to analyze.", file=sys.stderr)
            sys.exit(1)

    results = []
    for filepath in files_to_check:
        result = analyze_memory_file(filepath, project_root)
        results.append(result)

    duplicates = find_duplicates(results) if args.check_duplicates else []

    output = {
        "files": results,
        "duplicates": duplicates,
        "summary": {
            "total_files": len(results),
            "total_entries": sum(r.get("total_entries", 0) for r in results),
            "total_stale": sum(r.get("stale_entries", 0) for r in results),
            "total_duplicates": len(duplicates),
            "average_staleness": round(
                sum(r.get("average_staleness_score", 0) for r in results) / len(results), 1
            ) if results else 0,
        },
    }

    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print(f"\n{'=' * 60}")
        print("MEMORY STALENESS REPORT")
        print(f"{'=' * 60}")

        for result in results:
            filepath = result.get("filepath", "unknown")
            name = result.get("name", "unknown")
            avg = result.get("average_staleness_score", 0)
            stale = result.get("stale_entries", 0)
            total = result.get("total_entries", 0)
            status = "STALE" if stale > 0 else "OK"

            print(f"\n  [{status}] {name} ({filepath})")
            print(f"    Entries: {total}, Stale: {stale}, Avg Score: {avg}/25")

            for entry in result.get("entries", []):
                if entry.get("is_stale"):
                    print(f"    STALE: {entry['entry_preview'][:70]}...")
                    for ref in entry.get("missing_references", []):
                        print(f"      Missing {ref['type']}: {ref['ref']}")

        if duplicates:
            print(f"\n{'=' * 60}")
            print(f"DUPLICATES FOUND ({len(duplicates)})")
            print(f"{'=' * 60}")
            for dup in duplicates:
                print(f"\n  [{dup['type']}]")
                print(f"    File A: {dup['file_a']}")
                print(f"    File B: {dup['file_b']}")
                if "similarity" in dup:
                    print(f"    Similarity: {dup['similarity']}")

        summary = output["summary"]
        print(f"\n--- Summary ---")
        print(f"Files: {summary['total_files']}")
        print(f"Entries: {summary['total_entries']}")
        print(f"Stale: {summary['total_stale']}")
        print(f"Duplicates: {summary['total_duplicates']}")
        print(f"Average staleness score: {summary['average_staleness']}/25")


if __name__ == "__main__":
    main()
