#!/usr/bin/env python3
"""Analyze Claude Code session logs for usage patterns and automation opportunities.

Extracts comprehensive metrics from JSONL session logs including tool usage,
bash commands, workflow sequences, MCP calls, error patterns, and more.
Used by /optimize:discover, /optimize:audit, /optimize:skills, /optimize:hooks.
"""

import argparse
import json
import glob
import os
import sys
from collections import Counter
from datetime import datetime


def find_project_dir():
    """Find the Claude project directory for the current working directory."""
    cwd = os.getcwd()
    encoded = cwd.replace("/", "-").lstrip("-")
    base = os.path.expanduser("~/.claude/projects")

    if not os.path.isdir(base):
        print(f"No Claude projects directory found at {base}", file=sys.stderr)
        sys.exit(1)

    exact = os.path.join(base, encoded)
    if os.path.isdir(exact):
        return exact

    basename = os.path.basename(cwd)
    candidates = glob.glob(os.path.join(base, f"*{basename}*"))
    if candidates:
        return candidates[0]

    print(f"No project directory found for {cwd}", file=sys.stderr)
    sys.exit(1)


def analyze(project_dir, max_sessions=30):
    """Parse session JSONL files and extract comprehensive patterns."""
    logs = sorted(
        glob.glob(os.path.join(project_dir, "*.jsonl")),
        key=os.path.getmtime,
        reverse=True,
    )[:max_sessions]

    if not logs:
        print("No session logs found.")
        return

    # Counters
    tool_counts = Counter()
    bash_full_commands = Counter()
    bash_base_commands = Counter()
    file_edits = Counter()
    file_reads = Counter()
    glob_patterns = Counter()
    grep_patterns = Counter()
    mcp_tool_calls = Counter()
    toolsearch_queries = Counter()
    error_types = Counter()
    branches = set()

    # Per-session tracking
    tool_sequences = []
    session_summaries = []
    total_tool_calls = 0

    for log_path in logs:
        session_tools = []
        session_errors = 0
        session_id = os.path.splitext(os.path.basename(log_path))[0]

        try:
            with open(log_path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if not isinstance(entry, dict):
                        continue

                    # Extract git branch
                    gb = entry.get("gitBranch", "")
                    if gb:
                        branches.add(gb)

                    # Process assistant messages for tool_use blocks
                    if entry.get("type") == "assistant":
                        msg = entry.get("message", {})
                        content = msg.get("content", []) if isinstance(msg, dict) else []
                        if isinstance(content, list):
                            for block in content:
                                if not isinstance(block, dict):
                                    continue
                                if block.get("type") != "tool_use":
                                    continue

                                name = block.get("name", "unknown")
                                tool_counts[name] += 1
                                total_tool_calls += 1
                                session_tools.append(name)
                                inp = block.get("input", {})

                                if name == "Bash":
                                    cmd = inp.get("command", "").strip()
                                    if cmd:
                                        bash_full_commands[cmd[:150]] += 1
                                        parts = cmd.split()
                                        if parts:
                                            bash_base_commands[parts[0]] += 1

                                elif name == "Edit":
                                    fp = inp.get("file_path", "")
                                    if fp:
                                        file_edits[fp] += 1

                                elif name == "Write":
                                    fp = inp.get("file_path", "")
                                    if fp:
                                        file_edits[f"[Write] {fp}"] += 1

                                elif name == "Read":
                                    fp = inp.get("file_path", "")
                                    if fp:
                                        file_reads[fp] += 1

                                elif name == "Glob":
                                    pat = inp.get("pattern", "")
                                    if pat:
                                        glob_patterns[pat] += 1

                                elif name == "Grep":
                                    pat = inp.get("pattern", "")
                                    if pat:
                                        grep_patterns[pat[:80]] += 1

                                elif name == "ToolSearch":
                                    q = inp.get("query", "")
                                    if q:
                                        toolsearch_queries[q] += 1

                                elif name.startswith("mcp__"):
                                    mcp_tool_calls[name] += 1

                    # Process user messages for tool_result errors
                    if entry.get("type") == "user":
                        msg = entry.get("message", {})
                        content = msg.get("content", []) if isinstance(msg, dict) else []
                        if isinstance(content, list):
                            for block in content:
                                if not isinstance(block, dict):
                                    continue
                                if block.get("type") != "tool_result":
                                    continue
                                if not block.get("is_error", False):
                                    continue

                                err_content = block.get("content", "")
                                err_text = ""
                                if isinstance(err_content, str):
                                    err_text = err_content[:150]
                                elif isinstance(err_content, list):
                                    for sub in err_content:
                                        if isinstance(sub, dict) and sub.get("text"):
                                            err_text = sub["text"][:150]
                                            break
                                if err_text:
                                    error_types[err_text[:120]] += 1
                                session_errors += 1

        except (OSError, IOError):
            continue

        tool_sequences.append(session_tools)
        session_summaries.append({
            "id": session_id[:16],
            "tools": len(session_tools),
            "errors": session_errors,
            "size_kb": os.path.getsize(log_path) // 1024,
        })

    # Workflow sequences (bigrams and trigrams)
    bigram_counts = Counter()
    trigram_counts = Counter()
    for seq in tool_sequences:
        for i in range(len(seq) - 1):
            bigram_counts[(seq[i], seq[i + 1])] += 1
        for i in range(len(seq) - 2):
            trigram_counts[(seq[i], seq[i + 1], seq[i + 2])] += 1

    # Date range from file modification times
    mtimes = [os.path.getmtime(lp) for lp in logs]
    oldest = datetime.fromtimestamp(min(mtimes)).strftime("%Y-%m-%d")
    newest = datetime.fromtimestamp(max(mtimes)).strftime("%Y-%m-%d")

    # === Output ===
    sep = "=" * 70
    subsep = "-" * 60

    print(sep)
    print("SESSION LOG ANALYSIS")
    print(f"Sessions analyzed: {len(logs)}")
    print(f"Date range: {oldest} to {newest}")
    print(f"Total tool calls: {total_tool_calls}")
    print(sep)

    print(f"\n## 1. TOOL USAGE FREQUENCY")
    print(subsep)
    for tool, count in tool_counts.most_common(30):
        pct = count / total_tool_calls * 100 if total_tool_calls else 0
        print(f"  {tool:45s} {count:5d}  ({pct:.1f}%)")

    print(f"\n## 2. BASH BASE COMMANDS (top 25)")
    print(subsep)
    for cmd, count in bash_base_commands.most_common(25):
        print(f"  {count:4d}x  {cmd}")

    print(f"\n## 3. BASH FULL COMMANDS (repeated 2+, top 30)")
    print(subsep)
    for cmd, count in bash_full_commands.most_common(40):
        if count >= 2:
            print(f"  {count:4d}x  {cmd[:120]}")

    print(f"\n## 4. FILE EDIT FREQUENCY (top 25)")
    print(subsep)
    for fp, count in file_edits.most_common(25):
        print(f"  {count:4d}x  {fp}")

    print(f"\n## 5. FILE READ FREQUENCY (top 25)")
    print(subsep)
    for fp, count in file_reads.most_common(25):
        print(f"  {count:4d}x  {fp}")

    print(f"\n## 6. GLOB PATTERNS (top 15)")
    print(subsep)
    for pat, count in glob_patterns.most_common(15):
        print(f"  {count:4d}x  {pat}")

    print(f"\n## 7. GREP PATTERNS (top 15)")
    print(subsep)
    for pat, count in grep_patterns.most_common(15):
        print(f"  {count:4d}x  {pat}")

    print(f"\n## 8. MCP TOOL CALLS")
    print(subsep)
    if mcp_tool_calls:
        for tool, count in mcp_tool_calls.most_common():
            print(f"  {count:4d}x  {tool}")
    else:
        print("  (none)")

    print(f"\n## 9. TOOLSEARCH QUERIES (top 25)")
    print(subsep)
    for q, count in toolsearch_queries.most_common(25):
        print(f"  {count:4d}x  \"{q}\"")
    total_ts = sum(toolsearch_queries.values())
    select_count = sum(v for k, v in toolsearch_queries.items() if k.startswith("select:"))
    print(f"  Total ToolSearch calls: {total_ts} (select: {select_count}, keyword: {total_ts - select_count})")

    print(f"\n## 10. ERROR PATTERNS (top 20)")
    print(subsep)
    for err, count in error_types.most_common(20):
        print(f"  {count:4d}x  {err[:120]}")
    print(f"  Total errors: {sum(error_types.values())}")

    print(f"\n## 11. BRANCHES REFERENCED")
    print(subsep)
    for b in sorted(branches):
        print(f"  {b}")

    print(f"\n## 12. WORKFLOW BIGRAMS (top 20)")
    print(subsep)
    for (a, b), count in bigram_counts.most_common(20):
        print(f"  {count:4d}x  {a} -> {b}")

    print(f"\n## 13. WORKFLOW TRIGRAMS (top 20)")
    print(subsep)
    for (a, b, c), count in trigram_counts.most_common(20):
        print(f"  {count:4d}x  {a} -> {b} -> {c}")

    print(f"\n## 14. SESSION DISTRIBUTION")
    print(subsep)
    sizes = [s["size_kb"] for s in session_summaries]
    tools_per = [s["tools"] for s in session_summaries]
    print(f"  Session sizes (KB): min={min(sizes)}, max={max(sizes)}, avg={sum(sizes) // len(sizes)}")
    print(f"  Tool calls/session: min={min(tools_per)}, max={max(tools_per)}, avg={sum(tools_per) // len(tools_per)}")
    small = sum(1 for s in sizes if s < 5)
    medium = sum(1 for s in sizes if 5 <= s < 100)
    large = sum(1 for s in sizes if 100 <= s < 500)
    xlarge = sum(1 for s in sizes if s >= 500)
    print(f"  Size buckets: <5KB={small}, 5-100KB={medium}, 100-500KB={large}, 500KB+={xlarge}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze Claude Code session logs")
    parser.add_argument("--project-dir", help="Path to Claude project directory")
    parser.add_argument("--max-sessions", type=int, default=30, help="Max sessions to analyze (default: 30)")
    # Legacy positional args for backwards compatibility
    parser.add_argument("legacy_dir", nargs="?", help=argparse.SUPPRESS)
    parser.add_argument("legacy_max", nargs="?", type=int, help=argparse.SUPPRESS)
    args = parser.parse_args()

    project_dir = args.project_dir or args.legacy_dir or find_project_dir()
    max_sessions = args.max_sessions if args.max_sessions != 30 else (args.legacy_max or 30)
    analyze(project_dir, max_sessions)
