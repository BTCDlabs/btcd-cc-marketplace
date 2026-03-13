#!/usr/bin/env python3
"""Tests for memory_staleness.py."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from memory_staleness import (
    extract_references,
    analyze_memory_entry,
    find_duplicates,
)


class TestExtractReferences(unittest.TestCase):
    def test_file_paths(self):
        refs = extract_references("Check the file at `src/utils/helper.ts` for details")
        self.assertGreater(len(refs["file_paths"]), 0)

    def test_package_names(self):
        refs = extract_references("Install with npm install express")
        self.assertIn("express", refs["packages"])

    def test_identifiers(self):
        refs = extract_references("Use the `calculateTotal` function for pricing")
        self.assertIn("calculateTotal", refs["identifiers"])

    def test_empty_text(self):
        refs = extract_references("")
        self.assertEqual(len(refs["file_paths"]), 0)
        self.assertEqual(len(refs["packages"]), 0)
        self.assertEqual(len(refs["identifiers"]), 0)

    def test_import_patterns(self):
        refs = extract_references("import json\nfrom pathlib import Path")
        self.assertIn("json", refs["packages"])
        self.assertIn("pathlib", refs["packages"])


class TestAnalyzeMemoryEntry(unittest.TestCase):
    def test_no_references(self):
        result = analyze_memory_entry("Just a simple note about the project.", "/tmp")
        self.assertEqual(result["total_references"], 0)
        self.assertEqual(result["staleness_score"], 15)  # Neutral

    def test_entry_with_valid_reference(self):
        # Use a path that exists on the system
        result = analyze_memory_entry("Check the file at /usr/bin/env for details", "/")
        # /usr/bin/env should exist
        self.assertGreater(result["found_references"], 0)

    def test_entry_with_missing_reference(self):
        result = analyze_memory_entry(
            "Use the function at `src/nonexistent/file_xyz_123.ts`",
            "/tmp"
        )
        if result["total_references"] > 0:
            self.assertGreater(len(result["missing_references"]), 0)


class TestFindDuplicates(unittest.TestCase):
    def test_exact_duplicates(self):
        data = [
            {
                "filepath": "file1.md",
                "entries": [
                    {"entry_index": 0, "entry_preview": "always use bun instead of npm for package management"},
                ],
            },
            {
                "filepath": "file2.md",
                "entries": [
                    {"entry_index": 0, "entry_preview": "always use bun instead of npm for package management"},
                ],
            },
        ]
        duplicates = find_duplicates(data)
        self.assertGreater(len(duplicates), 0)
        self.assertEqual(duplicates[0]["type"], "exact")

    def test_no_duplicates(self):
        data = [
            {
                "filepath": "file1.md",
                "entries": [
                    {"entry_index": 0, "entry_preview": "this is about security configuration"},
                ],
            },
            {
                "filepath": "file2.md",
                "entries": [
                    {"entry_index": 0, "entry_preview": "python formatting uses black and ruff tools"},
                ],
            },
        ]
        duplicates = find_duplicates(data)
        self.assertEqual(len(duplicates), 0)

    def test_near_duplicates(self):
        data = [
            {
                "filepath": "file1.md",
                "entries": [
                    {"entry_index": 0, "entry_preview": "always use bun for package management instead of npm"},
                ],
            },
            {
                "filepath": "file2.md",
                "entries": [
                    {"entry_index": 0, "entry_preview": "always use bun for package management not npm"},
                ],
            },
        ]
        duplicates = find_duplicates(data)
        if duplicates:
            self.assertEqual(duplicates[0]["type"], "near_duplicate")


if __name__ == "__main__":
    unittest.main()
