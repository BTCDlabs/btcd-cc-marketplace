#!/usr/bin/env python3
"""Tests for skill_analyzer.py."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from skill_analyzer import (
    tokenize,
    jaccard_similarity,
    assess_trigger_quality,
    find_overlaps,
    analyze_skills,
)


class TestTokenize(unittest.TestCase):
    def test_basic_tokenization(self):
        tokens = tokenize("Use this skill for analyzing code quality")
        self.assertIn("skill", tokens)
        self.assertIn("analyzing", tokens)
        self.assertIn("code", tokens)
        self.assertIn("quality", tokens)
        # Stop words removed
        self.assertNotIn("this", tokens)
        self.assertNotIn("for", tokens)

    def test_empty_string(self):
        self.assertEqual(tokenize(""), [])

    def test_short_words_filtered(self):
        tokens = tokenize("a an the is it ok")
        self.assertEqual(tokens, [])

    def test_lowercase(self):
        tokens = tokenize("UPPERCASE Words HERE")
        for t in tokens:
            self.assertEqual(t, t.lower())


class TestJaccardSimilarity(unittest.TestCase):
    def test_identical(self):
        tokens = ["skill", "analyzer", "code"]
        self.assertEqual(jaccard_similarity(tokens, tokens), 1.0)

    def test_no_overlap(self):
        self.assertEqual(jaccard_similarity(["a", "b"], ["c", "d"]), 0.0)

    def test_partial_overlap(self):
        sim = jaccard_similarity(["a", "b", "c"], ["b", "c", "d"])
        self.assertAlmostEqual(sim, 2 / 4)  # 2 shared, 4 union

    def test_empty(self):
        self.assertEqual(jaccard_similarity([], []), 0.0)
        self.assertEqual(jaccard_similarity(["a"], []), 0.0)


class TestTriggerQuality(unittest.TestCase):
    def test_excellent_description(self):
        desc = ("Use when running /optimize:test to analyze test coverage. "
                "Triggers on test analysis or coverage checking. "
                "Do NOT trigger on general coding tasks.")
        result = assess_trigger_quality(desc)
        self.assertEqual(result["quality"], "excellent")
        self.assertTrue(result["has_negative_trigger"])
        self.assertTrue(result["has_positive_trigger"])
        self.assertEqual(len(result["issues"]), 0)

    def test_bloated_description(self):
        desc = " ".join(["word"] * 200)
        result = assess_trigger_quality(desc)
        self.assertEqual(result["quality"], "poor")
        self.assertTrue(any("too long" in i for i in result["issues"]))

    def test_short_description(self):
        desc = "A simple skill"
        result = assess_trigger_quality(desc)
        self.assertTrue(result["word_count"] < 20)

    def test_missing_negative_trigger(self):
        desc = "Use when running optimize to analyze code. Triggers on code analysis."
        result = assess_trigger_quality(desc)
        self.assertFalse(result["has_negative_trigger"])
        self.assertTrue(any("do not trigger" in i.lower() for i in result["issues"]))


class TestFindOverlaps(unittest.TestCase):
    def test_no_overlap(self):
        skills = [
            {"name": "a", "description": "Analyze security posture of the system"},
            {"name": "b", "description": "Format Python code with black and ruff"},
        ]
        overlaps = find_overlaps(skills, threshold=0.7)
        self.assertEqual(len(overlaps), 0)

    def test_high_overlap(self):
        skills = [
            {"name": "a", "description": "Analyze security posture including permissions and deny rules"},
            {"name": "b", "description": "Analyze security posture including permissions and allow rules"},
        ]
        overlaps = find_overlaps(skills, threshold=0.5)
        self.assertGreater(len(overlaps), 0)

    def test_empty_descriptions(self):
        skills = [
            {"name": "a", "description": ""},
            {"name": "b", "description": ""},
        ]
        overlaps = find_overlaps(skills)
        self.assertEqual(len(overlaps), 0)


class TestActualSkills(unittest.TestCase):
    """Test against actual plugin SKILL.md files."""

    def test_analyze_plugin_skills(self):
        skills_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "skills"
        )
        if not os.path.isdir(skills_dir):
            self.skipTest("Skills directory not found")

        import glob
        paths = sorted(glob.glob(os.path.join(skills_dir, "*/SKILL.md")))
        self.assertGreater(len(paths), 0)

        result = analyze_skills(paths)
        self.assertIn("skills", result)
        self.assertIn("overlaps", result)
        self.assertIn("summary", result)
        self.assertEqual(result["summary"]["total_skills"], len(paths))

        # Verify all skills have trigger quality assessment
        for skill in result["skills"]:
            self.assertIn("trigger_quality", skill)
            self.assertIn("quality", skill["trigger_quality"])


if __name__ == "__main__":
    unittest.main()
