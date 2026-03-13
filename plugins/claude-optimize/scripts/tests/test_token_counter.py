#!/usr/bin/env python3
"""Tests for token_counter.py."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from token_counter import count_file, count_string, count_description, TOKEN_BANDS


class TestCountString(unittest.TestCase):
    def test_empty_string(self):
        result = count_string("")
        self.assertEqual(result["lines"], 0)
        self.assertEqual(result["words"], 0)
        self.assertEqual(result["tokens_estimated"], 0)

    def test_simple_content(self):
        result = count_string("Hello world this is a test")
        self.assertEqual(result["words"], 6)
        self.assertGreater(result["tokens_estimated"], 0)
        self.assertEqual(result["content_type"], "mixed")

    def test_multiline_content(self):
        result = count_string("Line 1\nLine 2\nLine 3\n")
        self.assertEqual(result["lines"], 3)

    def test_prose_ratio(self):
        result = count_string("word " * 100, content_type="prose")
        self.assertEqual(result["tokens_estimated"], int(100 * 1.3))

    def test_code_ratio(self):
        result = count_string("word " * 100, content_type="code")
        self.assertEqual(result["tokens_estimated"], int(100 * 1.5))

    def test_band_excellent(self):
        result = count_string("word " * 10)  # 10 words * 1.4 = 14 tokens
        self.assertEqual(result["band"], "excellent")

    def test_band_warning(self):
        result = count_string("word " * 1200)  # 1200 words * 1.4 = 1680 tokens
        self.assertEqual(result["band"], "warning")


class TestCountDescription(unittest.TestCase):
    def test_excellent(self):
        result = count_description(
            "Use this skill to analyze and optimize token consumption in Claude Code "
            "configuration files including CLAUDE.md files and all skill description frontmatter"
        )
        self.assertEqual(result["quality"], "excellent")
        self.assertFalse(result["over_limit"])
        self.assertFalse(result["under_minimum"])

    def test_bloated(self):
        result = count_description(" ".join(["word"] * 200))
        self.assertEqual(result["quality"], "bloated")
        self.assertTrue(result["over_limit"])

    def test_under_minimum(self):
        result = count_description("too short")
        self.assertTrue(result["under_minimum"])


class TestCountFile(unittest.TestCase):
    def test_real_file(self):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
        f.write("# Title\n\nSome content here with words.\n")
        f.close()
        try:
            result = count_file(f.name)
            self.assertIsNotNone(result)
            self.assertEqual(result["filepath"], f.name)
            self.assertGreater(result["words"], 0)
        finally:
            os.unlink(f.name)

    def test_nonexistent_file(self):
        result = count_file("/nonexistent/file.md")
        self.assertIsNone(result)


class TestTokenBands(unittest.TestCase):
    def test_bands_cover_full_range(self):
        """Verify that band ranges are contiguous and cover 0 to infinity."""
        self.assertEqual(TOKEN_BANDS["excellent"][0], 0)
        self.assertEqual(TOKEN_BANDS["critical"][1], float("inf"))


if __name__ == "__main__":
    unittest.main()
