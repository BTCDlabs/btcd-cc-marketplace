#!/usr/bin/env python3
"""Tests for codebase_detector.py."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from codebase_detector import (
    detect_languages,
    detect_frameworks,
    detect_package_manager,
    detect_cicd,
    detect_build_tools,
    detect_services,
    detect_claude_config,
    detect_all,
)


class TestDetectLanguages(unittest.TestCase):
    def test_no_indicators(self):
        tmpdir = tempfile.mkdtemp()
        try:
            langs = detect_languages(tmpdir)
            self.assertEqual(len(langs), 0)
        finally:
            os.rmdir(tmpdir)

    def test_python_project(self):
        tmpdir = tempfile.mkdtemp()
        req_path = os.path.join(tmpdir, "requirements.txt")
        with open(req_path, "w") as f:
            f.write("flask==2.0\n")
        try:
            langs = detect_languages(tmpdir)
            lang_names = [l["language"] for l in langs]
            self.assertIn("Python", lang_names)
        finally:
            os.unlink(req_path)
            os.rmdir(tmpdir)

    def test_node_project(self):
        tmpdir = tempfile.mkdtemp()
        pkg_path = os.path.join(tmpdir, "package.json")
        with open(pkg_path, "w") as f:
            json.dump({"name": "test"}, f)
        try:
            langs = detect_languages(tmpdir)
            lang_names = [l["language"] for l in langs]
            self.assertIn("JavaScript/TypeScript", lang_names)
        finally:
            os.unlink(pkg_path)
            os.rmdir(tmpdir)


class TestDetectFrameworks(unittest.TestCase):
    def test_no_frameworks(self):
        tmpdir = tempfile.mkdtemp()
        try:
            frameworks = detect_frameworks(tmpdir)
            self.assertEqual(len(frameworks), 0)
        finally:
            os.rmdir(tmpdir)

    def test_flask_via_requirements(self):
        tmpdir = tempfile.mkdtemp()
        req_path = os.path.join(tmpdir, "requirements.txt")
        with open(req_path, "w") as f:
            f.write("flask==2.0\nrequests\n")
        try:
            frameworks = detect_frameworks(tmpdir)
            fw_names = [f["framework"] for f in frameworks]
            self.assertIn("Flask", fw_names)
        finally:
            os.unlink(req_path)
            os.rmdir(tmpdir)


class TestDetectPackageManager(unittest.TestCase):
    def test_npm(self):
        tmpdir = tempfile.mkdtemp()
        lock_path = os.path.join(tmpdir, "package-lock.json")
        with open(lock_path, "w") as f:
            f.write("{}")
        try:
            managers = detect_package_manager(tmpdir)
            mgr_names = [m["manager"] for m in managers]
            self.assertIn("npm", mgr_names)
        finally:
            os.unlink(lock_path)
            os.rmdir(tmpdir)

    def test_no_manager(self):
        tmpdir = tempfile.mkdtemp()
        try:
            managers = detect_package_manager(tmpdir)
            self.assertEqual(len(managers), 0)
        finally:
            os.rmdir(tmpdir)


class TestDetectCICD(unittest.TestCase):
    def test_github_actions(self):
        tmpdir = tempfile.mkdtemp()
        workflows = os.path.join(tmpdir, ".github", "workflows")
        os.makedirs(workflows)
        try:
            systems = detect_cicd(tmpdir)
            sys_names = [s["system"] for s in systems]
            self.assertIn("GitHub Actions", sys_names)
        finally:
            os.rmdir(workflows)
            os.rmdir(os.path.join(tmpdir, ".github"))
            os.rmdir(tmpdir)


class TestDetectBuildTools(unittest.TestCase):
    def test_makefile(self):
        tmpdir = tempfile.mkdtemp()
        make_path = os.path.join(tmpdir, "Makefile")
        with open(make_path, "w") as f:
            f.write("all:\n\techo hello\n")
        try:
            tools = detect_build_tools(tmpdir)
            tool_names = [t["tool"] for t in tools]
            self.assertIn("Make", tool_names)
        finally:
            os.unlink(make_path)
            os.rmdir(tmpdir)


class TestDetectServices(unittest.TestCase):
    def test_stripe_in_package_json(self):
        tmpdir = tempfile.mkdtemp()
        pkg_path = os.path.join(tmpdir, "package.json")
        with open(pkg_path, "w") as f:
            json.dump({"dependencies": {"stripe": "^10.0"}}, f)
        try:
            services = detect_services(tmpdir)
            svc_names = [s["service"] for s in services]
            self.assertIn("Stripe", svc_names)
        finally:
            os.unlink(pkg_path)
            os.rmdir(tmpdir)


class TestDetectClaudeConfig(unittest.TestCase):
    def test_no_config(self):
        tmpdir = tempfile.mkdtemp()
        try:
            config = detect_claude_config(tmpdir)
            self.assertEqual(len(config["claude_md"]), 0)
            self.assertEqual(len(config["settings"]), 0)
        finally:
            os.rmdir(tmpdir)


class TestDetectAll(unittest.TestCase):
    def test_nonexistent_dir(self):
        result = detect_all("/nonexistent/path")
        self.assertIn("error", result)

    def test_empty_dir(self):
        tmpdir = tempfile.mkdtemp()
        try:
            result = detect_all(tmpdir)
            self.assertEqual(result["primary_language"], "Unknown")
            self.assertIn("languages", result)
            self.assertIn("frameworks", result)
        finally:
            os.rmdir(tmpdir)

    def test_actual_repo(self):
        # Test on the actual repo root
        repo_root = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        ))
        result = detect_all(repo_root)
        self.assertNotIn("error", result)
        self.assertIn("claude_config", result)


if __name__ == "__main__":
    unittest.main()
