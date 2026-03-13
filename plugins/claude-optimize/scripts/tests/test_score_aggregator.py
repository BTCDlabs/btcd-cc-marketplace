#!/usr/bin/env python3
"""Tests for score_aggregator.py."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from score_aggregator import aggregate_scores, prioritize_actions, calculate_grade


class TestCalculateGrade(unittest.TestCase):
    def test_grade_a(self):
        self.assertEqual(calculate_grade(95), "A")
        self.assertEqual(calculate_grade(90), "A")

    def test_grade_b(self):
        self.assertEqual(calculate_grade(85), "B")
        self.assertEqual(calculate_grade(80), "B")

    def test_grade_f(self):
        self.assertEqual(calculate_grade(50), "F")
        self.assertEqual(calculate_grade(0), "F")

    def test_boundary(self):
        self.assertEqual(calculate_grade(89), "B")
        self.assertEqual(calculate_grade(90), "A")


class TestAggregateScores(unittest.TestCase):
    def test_perfect_scores(self):
        scores = {
            "claude_md_quality": 100,
            "security_posture": 100,
            "context_efficiency": 100,
            "hook_coverage": 100,
            "skill_quality": 100,
            "memory_hygiene": 100,
            "mcp_health": 100,
            "codebase_alignment": 100,
        }
        result = aggregate_scores(scores)
        self.assertEqual(result["overall_score"], 100.0)
        self.assertEqual(result["overall_grade"], "A")

    def test_zero_scores(self):
        scores = {
            "claude_md_quality": 0,
            "security_posture": 0,
        }
        result = aggregate_scores(scores)
        self.assertEqual(result["overall_score"], 0.0)
        self.assertEqual(result["overall_grade"], "F")

    def test_mixed_scores(self):
        scores = {
            "claude_md_quality": 90,
            "security_posture": 50,
            "context_efficiency": 70,
        }
        result = aggregate_scores(scores)
        self.assertGreater(result["overall_score"], 0)
        self.assertLess(result["overall_score"], 100)

    def test_missing_dimensions_reported(self):
        scores = {"claude_md_quality": 80}
        result = aggregate_scores(scores)
        self.assertGreater(len(result["dimensions_missing"]), 0)

    def test_custom_weights(self):
        scores = {"dim_a": 100, "dim_b": 0}
        weights = {"dim_a": 0.8, "dim_b": 0.2}
        result = aggregate_scores(scores, weights)
        self.assertAlmostEqual(result["overall_score"], 80.0)


class TestPrioritizeActions(unittest.TestCase):
    def test_low_score_high_priority(self):
        scores = {"security_posture": 20, "mcp_health": 80}
        actions = prioritize_actions(scores)
        self.assertGreater(len(actions), 0)
        # Security should be higher priority (lower score, higher weight)
        if len(actions) >= 2:
            self.assertGreaterEqual(actions[0]["priority_score"], actions[1]["priority_score"])

    def test_no_actions_for_high_scores(self):
        scores = {"security_posture": 90, "mcp_health": 95}
        actions = prioritize_actions(scores)
        self.assertEqual(len(actions), 0)

    def test_custom_actions(self):
        scores = {"security_posture": 50}
        actions_list = [{
            "dimension": "security_posture",
            "description": "Add deny rules",
            "effort": "low",
        }]
        actions = prioritize_actions(scores, actions=actions_list)
        self.assertEqual(len(actions), 1)
        self.assertGreater(actions[0]["priority_score"], 0)


if __name__ == "__main__":
    unittest.main()
