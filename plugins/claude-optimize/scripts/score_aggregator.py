#!/usr/bin/env python3
"""Aggregate weighted scores across optimization dimensions.

Calculates weighted overall scores, assigns grades, and prioritizes actions.
Replaces ad-hoc score calculation instructions in report.md, audit.md,
and report-aggregator.md agent.
"""

import argparse
import json
import sys


# Default weights from report.md
DEFAULT_WEIGHTS = {
    "claude_md_quality": 0.20,
    "security_posture": 0.20,
    "context_efficiency": 0.15,
    "hook_coverage": 0.10,
    "memory_hygiene": 0.10,
    "mcp_health": 0.10,
    "skill_quality": 0.10,
    "codebase_alignment": 0.05,
}

# Grade boundaries
GRADE_BOUNDARIES = [
    (90, "A"),
    (80, "B"),
    (70, "C"),
    (60, "D"),
    (0, "F"),
]


def calculate_grade(score):
    """Convert numeric score (0-100) to letter grade."""
    for threshold, grade in GRADE_BOUNDARIES:
        if score >= threshold:
            return grade
    return "F"


def aggregate_scores(dimension_scores, weights=None):
    """Calculate weighted aggregate score from dimension scores.

    Args:
        dimension_scores: Dict mapping dimension names to scores (0-100)
        weights: Dict mapping dimension names to weights (0.0-1.0).
                Uses DEFAULT_WEIGHTS if not provided.

    Returns dict with overall score, grade, and per-dimension breakdown.
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    # Validate weights sum to ~1.0
    weight_sum = sum(weights.values())
    if abs(weight_sum - 1.0) > 0.01:
        # Normalize weights
        weights = {k: v / weight_sum for k, v in weights.items()}

    weighted_scores = {}
    overall = 0.0

    for dimension, weight in weights.items():
        score = dimension_scores.get(dimension)
        if score is None:
            continue
        weighted = score * weight
        weighted_scores[dimension] = {
            "raw_score": score,
            "weight": weight,
            "weighted_score": round(weighted, 1),
            "grade": calculate_grade(score),
        }
        overall += weighted

    overall = round(overall, 1)

    return {
        "overall_score": overall,
        "overall_grade": calculate_grade(overall),
        "dimensions": weighted_scores,
        "dimensions_reported": len(weighted_scores),
        "dimensions_missing": [d for d in weights if d not in dimension_scores],
    }


def prioritize_actions(dimension_scores, weights=None, actions=None):
    """Prioritize improvement actions by impact.

    Uses formula: priority = (score_improvement_potential * weight) / effort
    where score_improvement_potential = 100 - current_score

    Args:
        dimension_scores: Dict mapping dimensions to scores
        weights: Weight dict (uses DEFAULT_WEIGHTS if None)
        actions: Optional list of action dicts with {dimension, description, effort}

    Returns sorted list of prioritized actions.
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    if actions is None:
        # Generate default actions for low-scoring dimensions
        actions = []
        for dimension, score in dimension_scores.items():
            if score < 70:
                actions.append({
                    "dimension": dimension,
                    "description": f"Improve {dimension.replace('_', ' ')}",
                    "effort": "medium",
                })

    effort_map = {"low": 1, "medium": 2, "high": 3}

    prioritized = []
    for action in actions:
        dim = action["dimension"]
        score = dimension_scores.get(dim, 50)
        weight = weights.get(dim, 0.1)
        improvement_potential = 100 - score
        effort = effort_map.get(action.get("effort", "medium"), 2)

        priority = (improvement_potential * weight) / effort

        prioritized.append({
            **action,
            "current_score": score,
            "improvement_potential": improvement_potential,
            "weight": weight,
            "priority_score": round(priority, 2),
        })

    return sorted(prioritized, key=lambda x: x["priority_score"], reverse=True)


def main():
    parser = argparse.ArgumentParser(description="Aggregate weighted optimization scores")
    parser.add_argument(
        "--scores", required=True,
        help='JSON string or file path with dimension scores, e.g. \'{"security_posture": 85, ...}\''
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--weights",
        help="JSON string or file path with custom weights"
    )
    parser.add_argument(
        "--actions",
        help="JSON string or file path with action items"
    )
    args = parser.parse_args()

    # Parse scores
    scores = _parse_json_arg(args.scores)
    weights = _parse_json_arg(args.weights) if args.weights else None
    actions = _parse_json_arg(args.actions) if args.actions else None

    result = aggregate_scores(scores, weights)
    if actions or any(s < 70 for s in scores.values()):
        result["prioritized_actions"] = prioritize_actions(scores, weights, actions)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"\n{'=' * 60}")
        print(f"OPTIMIZATION SCORE REPORT")
        print(f"{'=' * 60}")
        print(f"\n  Overall: {result['overall_score']}/100 (Grade: {result['overall_grade']})")

        print(f"\n  Dimension Breakdown:")
        for dim, data in result["dimensions"].items():
            label = dim.replace("_", " ").title()
            print(f"    {label:25s}  {data['raw_score']:3d}/100 ({data['grade']})  "
                  f"[weight: {data['weight']:.0%}, contribution: {data['weighted_score']:.1f}]")

        if result.get("dimensions_missing"):
            print(f"\n  Missing Dimensions: {', '.join(result['dimensions_missing'])}")

        if result.get("prioritized_actions"):
            print(f"\n  Priority Actions:")
            for i, action in enumerate(result["prioritized_actions"][:10], 1):
                print(f"    {i}. {action['description']} "
                      f"(current: {action['current_score']}, "
                      f"impact: {action['priority_score']:.1f})")


def _parse_json_arg(value):
    """Parse a JSON argument that could be a string or file path."""
    if value is None:
        return None
    # Try as file path first
    if os.path.isfile(value):
        with open(value, "r") as f:
            return json.load(f)
    # Try as JSON string
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        print(f"Error: Could not parse JSON: {value}", file=sys.stderr)
        sys.exit(1)


# Need os for _parse_json_arg
import os


if __name__ == "__main__":
    main()
