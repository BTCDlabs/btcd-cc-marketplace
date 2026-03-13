#!/usr/bin/env python3
"""Analyze skill descriptions for quality, overlap, and trigger effectiveness.

Performs:
- Word count and quality band assessment
- Overlap/redundancy detection via Jaccard similarity
- Trigger quality scoring (excellent/good/fair/poor)
- Gap analysis when combined with session data

Replaces ad-hoc tokenization, similarity calculation, and description analysis
in discover-analyzer/SKILL.md and skills.md command.
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

# Stop words for similarity calculation
STOP_WORDS = frozenset([
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "must",
    "to", "of", "in", "for", "on", "with", "at", "by", "from", "as",
    "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such",
    "no", "not", "only", "own", "same", "so", "than", "too", "very",
    "and", "but", "or", "nor", "if", "while", "that", "this", "these",
    "those", "it", "its", "what", "which", "who", "whom",
    "use", "used", "using", "trigger", "when", "do", "dont", "don't",
])


def tokenize(text):
    """Tokenize text into lowercase words, removing stop words and punctuation."""
    words = re.findall(r'[a-z][a-z0-9_-]*', text.lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 2]


def jaccard_similarity(tokens_a, tokens_b):
    """Calculate Jaccard similarity between two token sets."""
    set_a = set(tokens_a)
    set_b = set(tokens_b)
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def assess_trigger_quality(description):
    """Assess the trigger quality of a skill description.

    Returns quality rating and list of issues.
    """
    word_count = len(description.split())
    issues = []
    quality = "excellent"

    # Check word count
    if word_count > 150:
        issues.append(f"Description too long ({word_count} words, max 150)")
        quality = "poor"
    elif word_count > 100:
        issues.append(f"Description verbose ({word_count} words, prefer <100)")
        if quality != "poor":
            quality = "fair"

    if word_count < 20:
        issues.append(f"Description too short ({word_count} words, min 20)")
        if quality not in ("poor",):
            quality = "fair"

    # Check for negative triggers ("do not trigger" clauses)
    has_negative = bool(re.search(
        r'(?:do\s+not\s+trigger|don\'?t\s+trigger|not\s+(?:for|when)|do\s+not\s+use)',
        description, re.I
    ))
    if not has_negative:
        issues.append("Missing 'do not trigger' clause (helps prevent false activations)")
        if quality == "excellent":
            quality = "good"

    # Check for specific trigger conditions
    has_triggers = bool(re.search(
        r'(?:trigger\s+when|use\s+when|triggers?\s+on|invoke\s+when)',
        description, re.I
    ))
    if not has_triggers:
        issues.append("No explicit trigger conditions specified")
        if quality in ("excellent", "good"):
            quality = "fair"

    return {
        "quality": quality,
        "word_count": word_count,
        "has_negative_trigger": has_negative,
        "has_positive_trigger": has_triggers,
        "issues": issues,
    }


def find_overlaps(skills, threshold=0.7):
    """Find overlapping skill descriptions using Jaccard similarity.

    Args:
        skills: List of skill dicts with 'name' and 'description'
        threshold: Similarity threshold (default 0.7 per discover-analyzer)

    Returns list of overlap pairs.
    """
    overlaps = []

    # Tokenize all descriptions
    tokenized = []
    for skill in skills:
        desc = skill.get("description", "")
        tokens = tokenize(desc)
        tokenized.append({
            "name": skill["name"],
            "tokens": tokens,
            "description": desc,
        })

    # Compare all pairs
    for i in range(len(tokenized)):
        for j in range(i + 1, len(tokenized)):
            a = tokenized[i]
            b = tokenized[j]
            sim = jaccard_similarity(a["tokens"], b["tokens"])
            if sim >= threshold:
                overlaps.append({
                    "skill_a": a["name"],
                    "skill_b": b["name"],
                    "similarity": round(sim, 3),
                    "shared_keywords": sorted(set(a["tokens"]) & set(b["tokens"])),
                })

    return sorted(overlaps, key=lambda x: x["similarity"], reverse=True)


def analyze_skills(skill_paths):
    """Analyze a list of skill SKILL.md files.

    Args:
        skill_paths: List of SKILL.md file paths

    Returns comprehensive analysis dict.
    """
    skills = []

    for path in skill_paths:
        fm = parse_frontmatter(path)
        if fm is None:
            continue

        name = fm.get("name", os.path.basename(os.path.dirname(path)))
        description = fm.get("description", "")

        trigger_assessment = assess_trigger_quality(description)

        skills.append({
            "name": name,
            "path": path,
            "description": description,
            "trigger_quality": trigger_assessment,
        })

    # Find overlaps
    overlaps = find_overlaps(skills)

    # Summary statistics
    quality_counts = {"excellent": 0, "good": 0, "fair": 0, "poor": 0}
    for skill in skills:
        q = skill["trigger_quality"]["quality"]
        quality_counts[q] = quality_counts.get(q, 0) + 1

    return {
        "skills": skills,
        "overlaps": overlaps,
        "summary": {
            "total_skills": len(skills),
            "quality_distribution": quality_counts,
            "total_overlaps": len(overlaps),
            "avg_description_words": round(
                sum(s["trigger_quality"]["word_count"] for s in skills) / len(skills), 1
            ) if skills else 0,
        },
    }


def discover_skill_paths(search_dirs):
    """Find all SKILL.md files in search directories."""
    paths = []
    for search_dir in search_dirs:
        search_dir = os.path.expanduser(search_dir)
        if not os.path.isdir(search_dir):
            continue
        for skill_md in sorted(glob.glob(os.path.join(search_dir, "*", "SKILL.md"))):
            paths.append(skill_md)
    return paths


def main():
    parser = argparse.ArgumentParser(description="Analyze skill descriptions for quality and overlap")
    parser.add_argument("skill_files", nargs="*", help="SKILL.md file paths to analyze")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--search-dirs", nargs="+",
        help="Directories to search for SKILL.md files"
    )
    parser.add_argument(
        "--threshold", type=float, default=0.7,
        help="Similarity threshold for overlap detection (default: 0.7)"
    )
    parser.add_argument(
        "--auto-discover", action="store_true",
        help="Auto-discover skills from standard paths"
    )
    parser.add_argument(
        "--summary", action="store_true",
        help="With --json, output only the summary section"
    )
    args = parser.parse_args()

    paths = list(args.skill_files)

    if args.search_dirs:
        paths.extend(discover_skill_paths(args.search_dirs))

    if args.auto_discover or not paths:
        default_dirs = [
            ".claude/skills",
            os.path.expanduser("~/.claude/skills"),
        ]
        plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
        if plugin_root:
            default_dirs.append(os.path.join(plugin_root, "skills"))
        paths.extend(discover_skill_paths(default_dirs))

    if not paths:
        print("No SKILL.md files found to analyze.", file=sys.stderr)
        sys.exit(1)

    # Deduplicate
    paths = list(dict.fromkeys(paths))

    result = analyze_skills(paths)

    if args.json:
        output = result["summary"] if args.summary else result
        print(json.dumps(output, indent=2))
    else:
        print(f"\n{'=' * 60}")
        print("SKILL ANALYSIS REPORT")
        print(f"{'=' * 60}")

        summary = result["summary"]
        print(f"\n  Total skills: {summary['total_skills']}")
        print(f"  Avg description words: {summary['avg_description_words']}")
        print(f"  Quality distribution: {json.dumps(summary['quality_distribution'])}")

        print(f"\n  Per-Skill Assessment:")
        print(f"  {'-' * 55}")
        for skill in result["skills"]:
            tq = skill["trigger_quality"]
            status = {"excellent": "OK", "good": "OK", "fair": "WARN", "poor": "FAIL"}[tq["quality"]]
            print(f"\n  [{status:4s}] {skill['name']}")
            print(f"    Quality: {tq['quality']}, Words: {tq['word_count']}")
            for issue in tq["issues"]:
                print(f"    - {issue}")

        if result["overlaps"]:
            print(f"\n  Overlapping Skills ({len(result['overlaps'])}):")
            print(f"  {'-' * 55}")
            for overlap in result["overlaps"]:
                print(f"\n  {overlap['skill_a']} <-> {overlap['skill_b']}")
                print(f"    Similarity: {overlap['similarity']:.1%}")
                print(f"    Shared keywords: {', '.join(overlap['shared_keywords'][:10])}")


if __name__ == "__main__":
    main()
