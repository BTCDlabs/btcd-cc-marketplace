#!/usr/bin/env python3
"""Tests for frontmatter_parser.py."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from frontmatter_parser import parse_frontmatter, parse_frontmatter_glob


class TestParseFrontmatter(unittest.TestCase):
    def _write_temp(self, content):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
        f.write(content)
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_basic_frontmatter(self):
        path = self._write_temp("---\nname: test\ndescription: A test skill\ntype: skill\n---\n\nBody content here.\n")
        result = parse_frontmatter(path)
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "test")
        self.assertEqual(result["description"], "A test skill")
        self.assertEqual(result["type"], "skill")
        self.assertIn("Body content here.", result["body"])

    def test_multiline_description(self):
        path = self._write_temp("---\nname: test\ndescription: >\n  This is a long\n  multiline description\n---\n\nBody.\n")
        result = parse_frontmatter(path)
        self.assertIn("This is a long", result["description"])
        self.assertIn("multiline description", result["description"])

    def test_no_frontmatter(self):
        path = self._write_temp("# Just a markdown file\n\nNo frontmatter here.\n")
        result = parse_frontmatter(path)
        self.assertIsNotNone(result)
        self.assertTrue(result.get("_no_frontmatter"))
        self.assertIn("Just a markdown file", result["body"])

    def test_empty_file(self):
        path = self._write_temp("")
        result = parse_frontmatter(path)
        self.assertIsNotNone(result)

    def test_quoted_values(self):
        path = self._write_temp("---\nname: 'quoted-name'\ndescription: \"double quoted\"\n---\n\nBody.\n")
        result = parse_frontmatter(path)
        self.assertEqual(result["name"], "quoted-name")
        self.assertEqual(result["description"], "double quoted")

    def test_filepath_in_result(self):
        path = self._write_temp("---\nname: test\n---\nBody.\n")
        result = parse_frontmatter(path)
        self.assertEqual(result["_filepath"], path)

    def test_nonexistent_file(self):
        result = parse_frontmatter("/nonexistent/file.md")
        self.assertIsNone(result)

    def test_glob_pattern(self):
        tmpdir = tempfile.mkdtemp()
        self.addCleanup(lambda: os.rmdir(tmpdir))
        path = os.path.join(tmpdir, "test.md")
        with open(path, "w") as f:
            f.write("---\nname: globtest\n---\nBody.\n")
        self.addCleanup(os.unlink, path)

        results = parse_frontmatter_glob(os.path.join(tmpdir, "*.md"))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "globtest")


class TestActualSkillFiles(unittest.TestCase):
    """Test against the actual SKILL.md files in the repo."""

    def test_all_skill_files_parse(self):
        skills_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "skills"
        )
        if not os.path.isdir(skills_dir):
            self.skipTest("Skills directory not found")

        import glob
        skill_files = glob.glob(os.path.join(skills_dir, "*/SKILL.md"))
        self.assertGreater(len(skill_files), 0, "No SKILL.md files found")

        for skill_file in skill_files:
            result = parse_frontmatter(skill_file)
            self.assertIsNotNone(result, f"Failed to parse {skill_file}")
            self.assertIn("name", result, f"Missing 'name' in {skill_file}")
            self.assertIn("description", result, f"Missing 'description' in {skill_file}")
            self.assertTrue(len(result["description"]) > 0, f"Empty description in {skill_file}")


if __name__ == "__main__":
    unittest.main()
