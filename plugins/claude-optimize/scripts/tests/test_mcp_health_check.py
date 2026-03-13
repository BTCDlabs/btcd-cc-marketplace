#!/usr/bin/env python3
"""Tests for mcp_health_check.py."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mcp_health_check import (
    check_command_exists,
    check_env_vars,
    estimate_tool_count,
    check_server_health,
    analyze_mcp_config,
    KNOWN_SERVERS,
)


class TestCheckCommandExists(unittest.TestCase):
    def test_existing_command(self):
        self.assertTrue(check_command_exists("python3"))

    def test_nonexistent_command(self):
        self.assertFalse(check_command_exists("nonexistent_command_xyz"))


class TestCheckEnvVars(unittest.TestCase):
    def test_set_var(self):
        os.environ["TEST_MCP_VAR"] = "value"
        try:
            result = check_env_vars({"TEST_MCP_VAR": "value"})
            self.assertTrue(result["TEST_MCP_VAR"])
        finally:
            del os.environ["TEST_MCP_VAR"]

    def test_unset_var(self):
        result = check_env_vars({"NONEXISTENT_VAR_XYZ": "value"})
        self.assertFalse(result["NONEXISTENT_VAR_XYZ"])

    def test_empty_config(self):
        result = check_env_vars({})
        self.assertEqual(len(result), 0)


class TestEstimateToolCount(unittest.TestCase):
    def test_known_server(self):
        count, source = estimate_tool_count("filesystem-server", {})
        self.assertGreater(count, 0)
        self.assertEqual(source, "catalog")

    def test_unknown_server(self):
        count, source = estimate_tool_count("custom-unknown-xyz", {"args": []})
        self.assertEqual(source, "default")

    def test_server_with_args(self):
        count, source = estimate_tool_count("custom-xyz", {"args": ["a", "b", "c", "d", "e"]})
        self.assertEqual(source, "heuristic")
        self.assertGreater(count, 5)


class TestCheckServerHealth(unittest.TestCase):
    def test_healthy_server(self):
        result = check_server_health("test", {"command": "python3", "args": []})
        self.assertEqual(result["status"], "healthy")
        self.assertEqual(len(result["issues"]), 0)

    def test_missing_command(self):
        result = check_server_health("test", {"command": "nonexistent_xyz", "args": []})
        self.assertEqual(result["status"], "unhealthy")
        self.assertGreater(len(result["issues"]), 0)

    def test_missing_env_var(self):
        result = check_server_health("test", {
            "command": "python3",
            "env": {"NONEXISTENT_API_KEY": "required"},
        })
        self.assertEqual(result["status"], "degraded")

    def test_no_command(self):
        result = check_server_health("test", {})
        self.assertEqual(result["status"], "unhealthy")


class TestAnalyzeMcpConfig(unittest.TestCase):
    def test_valid_config(self):
        config = {
            "mcpServers": {
                "test-server": {
                    "command": "python3",
                    "args": ["-m", "test_server"],
                }
            }
        }
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(config, f)
        f.close()
        try:
            result = analyze_mcp_config(f.name)
            self.assertIn("servers", result)
            self.assertEqual(len(result["servers"]), 1)
            self.assertIn("summary", result)
            self.assertIn("score", result["summary"])
        finally:
            os.unlink(f.name)

    def test_nonexistent_config(self):
        result = analyze_mcp_config("/nonexistent/mcp.json")
        self.assertIn("error", result)

    def test_empty_config(self):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump({"mcpServers": {}}, f)
        f.close()
        try:
            result = analyze_mcp_config(f.name)
            self.assertEqual(len(result["servers"]), 0)
            self.assertEqual(result["summary"]["score"], 100)
        finally:
            os.unlink(f.name)


class TestCheckTrustSettings(unittest.TestCase):
    def test_no_settings_file(self):
        from mcp_health_check import check_trust_settings
        result = check_trust_settings("/nonexistent/settings.json")
        self.assertFalse(result["enableAllProjectMcpServers"])
        self.assertEqual(len(result["issues"]), 0)

    def test_trust_enabled(self):
        from mcp_health_check import check_trust_settings
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump({"enableAllProjectMcpServers": True}, f)
        f.close()
        try:
            result = check_trust_settings(f.name)
            self.assertTrue(result["enableAllProjectMcpServers"])
            self.assertGreater(len(result["issues"]), 0)
            self.assertEqual(result["issues"][0]["severity"], "critical")
        finally:
            os.unlink(f.name)

    def test_trust_disabled(self):
        from mcp_health_check import check_trust_settings
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump({"enableAllProjectMcpServers": False}, f)
        f.close()
        try:
            result = check_trust_settings(f.name)
            self.assertFalse(result["enableAllProjectMcpServers"])
            self.assertEqual(len(result["issues"]), 0)
        finally:
            os.unlink(f.name)


if __name__ == "__main__":
    unittest.main()
