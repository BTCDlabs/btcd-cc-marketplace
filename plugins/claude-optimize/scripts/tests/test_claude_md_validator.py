#!/usr/bin/env python3
"""Tests for claude_md_validator.py."""

import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from claude_md_validator import (
    extract_commands_from_claude_md,
    extract_file_paths_from_claude_md,
    extract_package_json_scripts,
    extract_makefile_targets,
    validate_commands,
    validate_file_paths,
    score_claude_md,
)


class TestExtractCommands(unittest.TestCase):
    def _write_temp(self, content):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
        f.write(content)
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_fenced_code_block(self):
        path = self._write_temp("# Commands\n\n```bash\nnpm test\nnpm run build\n```\n")
        cmds = extract_commands_from_claude_md(path)
        self.assertEqual(len(cmds), 2)
        self.assertEqual(cmds[0]["command"], "npm test")
        self.assertEqual(cmds[1]["command"], "npm run build")

    def test_inline_command(self):
        path = self._write_temp("Run `npm test` to test and `make build` to build.\n")
        cmds = extract_commands_from_claude_md(path)
        self.assertEqual(len(cmds), 2)

    def test_no_commands(self):
        path = self._write_temp("# Just some docs\n\nNo commands here.\n")
        cmds = extract_commands_from_claude_md(path)
        self.assertEqual(len(cmds), 0)

    def test_comment_ignored(self):
        path = self._write_temp("```bash\n# this is a comment\nnpm test\n```\n")
        cmds = extract_commands_from_claude_md(path)
        self.assertEqual(len(cmds), 1)


class TestExtractFilePaths(unittest.TestCase):
    def _write_temp(self, content):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
        f.write(content)
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_backtick_paths(self):
        path = self._write_temp("Files: `src/utils/helper.ts` and `config/settings.json`\n")
        paths = extract_file_paths_from_claude_md(path)
        self.assertIn("src/utils/helper.ts", paths)
        self.assertIn("config/settings.json", paths)

    def test_no_paths(self):
        path = self._write_temp("No file paths here.\n")
        paths = extract_file_paths_from_claude_md(path)
        self.assertEqual(len(paths), 0)


class TestValidateCommands(unittest.TestCase):
    def test_validate_npm_script(self):
        tmpdir = tempfile.mkdtemp()
        pkg_path = os.path.join(tmpdir, "package.json")
        with open(pkg_path, "w") as f:
            json.dump({"scripts": {"test": "jest", "build": "tsc"}}, f)
        self.addCleanup(shutil.rmtree, tmpdir)

        commands = [{"command": "npm test", "source": "test", "file": "CLAUDE.md"}]
        results = validate_commands(commands, tmpdir)
        self.assertEqual(results[0]["status"], "valid")

    def test_validate_invalid_npm_script(self):
        tmpdir = tempfile.mkdtemp()
        pkg_path = os.path.join(tmpdir, "package.json")
        with open(pkg_path, "w") as f:
            json.dump({"scripts": {"test": "jest"}}, f)
        self.addCleanup(shutil.rmtree, tmpdir)

        commands = [{"command": "npm run nonexistent", "source": "test", "file": "CLAUDE.md"}]
        results = validate_commands(commands, tmpdir)
        self.assertEqual(results[0]["status"], "invalid")


class TestValidateFilePaths(unittest.TestCase):
    def test_existing_path(self):
        tmpdir = tempfile.mkdtemp()
        test_file = os.path.join(tmpdir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")
        self.addCleanup(shutil.rmtree, tmpdir)

        results = validate_file_paths(["test.txt"], tmpdir)
        self.assertTrue(results[0]["exists"])

    def test_missing_path(self):
        results = validate_file_paths(["nonexistent/file.txt"], "/tmp")
        self.assertFalse(results[0]["exists"])


class TestScoreClaudeMd(unittest.TestCase):
    def _write_temp(self, content, tmpdir=None):
        if tmpdir is None:
            tmpdir = tempfile.mkdtemp()
        path = os.path.join(tmpdir, "CLAUDE.md")
        with open(path, "w") as f:
            f.write(content)
        return path, tmpdir

    def test_good_claude_md(self):
        content = """# Project

## Commands

```bash
npm test
npm run build
npm run lint
```

## Architecture

The project has the following structure:
- `src/` - Source code
- `tests/` - Test files

## Gotchas

Warning: The API rate limits are strict.
Note: Always run migrations before testing.

## Important Notes

Known issue: The cache invalidation is tricky.
"""
        path, tmpdir = self._write_temp(content)
        try:
            result = score_claude_md(path, tmpdir)
            self.assertIn("total", result)
            self.assertIn("grade", result)
            self.assertGreater(result["total"], 0)
        finally:
            os.unlink(path)
            os.rmdir(tmpdir)

    def test_empty_claude_md(self):
        path, tmpdir = self._write_temp("")
        try:
            result = score_claude_md(path, tmpdir)
            # Empty file still gets conciseness (15) + currency neutral (10) + actionability base (5) = 30
            self.assertLess(result["total"], 50)
            self.assertEqual(result["grade"], "F")
        finally:
            os.unlink(path)
            os.rmdir(tmpdir)

    def test_nonexistent_file(self):
        result = score_claude_md("/nonexistent/CLAUDE.md", "/tmp")
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
