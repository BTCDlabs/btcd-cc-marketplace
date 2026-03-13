#!/usr/bin/env python3
"""Tests for env_inventory.py."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from env_inventory import (
    find_skills,
    find_agents,
    find_hooks,
    find_mcp_servers,
)


class TestFindSkills(unittest.TestCase):
    def test_find_plugin_skills(self):
        skills_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "skills"
        )
        if not os.path.isdir(skills_dir):
            self.skipTest("Skills directory not found")

        skills = find_skills([skills_dir])
        self.assertGreater(len(skills), 0)
        for skill in skills:
            self.assertIn("name", skill)
            self.assertIn("description", skill)
            self.assertIn("description_words", skill)
            self.assertIn("path", skill)

    def test_nonexistent_path(self):
        skills = find_skills(["/nonexistent/path"])
        self.assertEqual(len(skills), 0)

    def test_deduplication(self):
        skills_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "skills"
        )
        if not os.path.isdir(skills_dir):
            self.skipTest("Skills directory not found")

        # Same path twice should not duplicate
        skills = find_skills([skills_dir, skills_dir])
        names = [s["name"] for s in skills]
        self.assertEqual(len(names), len(set(names)))


class TestFindAgents(unittest.TestCase):
    def test_find_plugin_agents(self):
        agents_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "agents"
        )
        if not os.path.isdir(agents_dir):
            self.skipTest("Agents directory not found")

        agents = find_agents([agents_dir])
        self.assertGreater(len(agents), 0)
        for agent in agents:
            self.assertIn("name", agent)


class TestFindHooks(unittest.TestCase):
    def test_valid_settings(self):
        settings = {
            "hooks": {
                "PostToolUse": [
                    {
                        "matcher": "Write|Edit",
                        "hooks": [
                            {"type": "command", "command": "prettier", "timeout": 10}
                        ]
                    }
                ]
            }
        }
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(settings, f)
        f.close()
        try:
            hooks = find_hooks([f.name])
            self.assertEqual(len(hooks), 1)
            self.assertEqual(hooks[0]["event"], "PostToolUse")
            self.assertEqual(hooks[0]["matcher"], "Write|Edit")
        finally:
            os.unlink(f.name)

    def test_invalid_settings(self):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        f.write("not valid json")
        f.close()
        try:
            hooks = find_hooks([f.name])
            self.assertEqual(len(hooks), 0)
        finally:
            os.unlink(f.name)

    def test_nonexistent_file(self):
        hooks = find_hooks(["/nonexistent/settings.json"])
        self.assertEqual(len(hooks), 0)


class TestFindMcpServers(unittest.TestCase):
    def test_valid_mcp_config(self):
        config = {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@anthropic-ai/mcp-fs"],
                    "env": {"MCP_TOKEN": "xxx"},
                }
            }
        }
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(config, f)
        f.close()
        try:
            servers = find_mcp_servers([f.name])
            self.assertEqual(len(servers), 1)
            self.assertEqual(servers[0]["name"], "filesystem")
            self.assertEqual(servers[0]["command"], "npx")
            self.assertIn("MCP_TOKEN", servers[0]["env"])
        finally:
            os.unlink(f.name)

    def test_empty_config(self):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump({}, f)
        f.close()
        try:
            servers = find_mcp_servers([f.name])
            self.assertEqual(len(servers), 0)
        finally:
            os.unlink(f.name)


if __name__ == "__main__":
    unittest.main()
