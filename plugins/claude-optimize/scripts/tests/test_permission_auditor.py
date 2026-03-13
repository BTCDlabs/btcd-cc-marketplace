#!/usr/bin/env python3
"""Tests for permission_auditor.py."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from permission_auditor import (
    audit_deny_rules,
    audit_allow_rules,
    calculate_security_score,
    audit_settings,
    CRITICAL_DENY_RULES,
)


class TestAuditDenyRules(unittest.TestCase):
    def test_empty_deny_rules(self):
        result = audit_deny_rules({"deny": []})
        self.assertEqual(result["total_deny_rules"], 0)
        self.assertEqual(len(result["missing_critical"]), len(CRITICAL_DENY_RULES))

    def test_full_deny_rules(self):
        deny_list = [r["pattern"] for r in CRITICAL_DENY_RULES]
        result = audit_deny_rules({"deny": deny_list})
        self.assertEqual(len(result["missing_critical"]), 0)

    def test_partial_deny_rules(self):
        result = audit_deny_rules({"deny": ["rm -rf /", "chmod 777"]})
        self.assertEqual(result["total_deny_rules"], 2)
        self.assertGreater(len(result["missing_critical"]), 0)

    def test_no_deny_key(self):
        result = audit_deny_rules({})
        self.assertEqual(result["total_deny_rules"], 0)


class TestAuditAllowRules(unittest.TestCase):
    def test_dangerous_allow(self):
        result = audit_allow_rules({"allow": ["Bash(*)"]})
        self.assertEqual(len(result["dangerous"]), 1)
        self.assertEqual(result["dangerous"][0]["risk"], "critical")

    def test_safe_allow(self):
        result = audit_allow_rules({"allow": ["Bash(git:*)"]})
        self.assertEqual(len(result["dangerous"]), 0)
        self.assertEqual(len(result["safe"]), 1)

    def test_mixed_allow(self):
        result = audit_allow_rules({"allow": ["Bash(*)", "Bash(git:*)", "Bash(custom:*)"]})
        self.assertEqual(len(result["dangerous"]), 1)
        self.assertEqual(len(result["safe"]), 1)
        self.assertEqual(len(result["custom"]), 1)

    def test_no_allow_rules(self):
        result = audit_allow_rules({})
        self.assertEqual(result["total_allow_rules"], 0)


class TestCalculateSecurityScore(unittest.TestCase):
    def test_perfect_score(self):
        deny_findings = {
            "total_deny_rules": 10,
            "missing_critical": [],
            "missing_high": [],
            "has_sensitive_file_protection": True,
            "sensitive_patterns_covered": 7,
            "sensitive_patterns_total": 7,
        }
        allow_findings = {
            "total_allow_rules": 5,
            "dangerous": [],
            "safe": ["Bash(git:*)"],
            "custom": [],
        }
        score = calculate_security_score(deny_findings, allow_findings)
        self.assertGreaterEqual(score, 90)

    def test_worst_score(self):
        deny_findings = {
            "total_deny_rules": 0,
            "missing_critical": CRITICAL_DENY_RULES,
            "missing_high": [{"pattern": "x"}] * 5,
            "has_sensitive_file_protection": False,
            "sensitive_patterns_covered": 0,
            "sensitive_patterns_total": 7,
        }
        allow_findings = {
            "total_allow_rules": 1,
            "dangerous": [{"pattern": "Bash(*)", "risk": "critical", "why": "bad"}],
            "safe": [],
            "custom": [],
        }
        score = calculate_security_score(deny_findings, allow_findings)
        self.assertLessEqual(score, 30)


class TestAuditSettings(unittest.TestCase):
    def test_nonexistent_file(self):
        result = audit_settings("/nonexistent/settings.json")
        self.assertIn("error", result)
        self.assertEqual(result["score"], 0)

    def test_valid_settings(self):
        settings = {
            "deny": ["rm -rf /", "chmod 777"],
            "allow": ["Bash(git:*)"],
        }
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(settings, f)
        f.close()
        try:
            result = audit_settings(f.name)
            self.assertIn("score", result)
            self.assertIn("grade", result)
            self.assertGreater(result["score"], 0)
        finally:
            os.unlink(f.name)


class TestCheckEnvProtection(unittest.TestCase):
    def test_no_hooks(self):
        from permission_auditor import check_env_protection
        result = check_env_protection({})
        self.assertFalse(result["has_protection"])
        self.assertEqual(len(result["protection_hooks"]), 0)

    def test_with_protection_hook(self):
        from permission_auditor import check_env_protection
        settings = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Write|Edit",
                        "hooks": [
                            {"type": "command", "command": "check-no-env-write .env"}
                        ]
                    }
                ]
            }
        }
        result = check_env_protection(settings)
        self.assertTrue(result["has_protection"])
        self.assertGreater(len(result["protection_hooks"]), 0)

    def test_unrelated_hook(self):
        from permission_auditor import check_env_protection
        settings = {
            "hooks": {
                "PostToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": [
                            {"type": "command", "command": "echo done"}
                        ]
                    }
                ]
            }
        }
        result = check_env_protection(settings)
        self.assertFalse(result["has_protection"])


class TestCheckPrecompactHook(unittest.TestCase):
    def test_no_precompact(self):
        from permission_auditor import check_precompact_hook
        result = check_precompact_hook({})
        self.assertFalse(result["has_precompact_hook"])

    def test_with_precompact(self):
        from permission_auditor import check_precompact_hook
        settings = {
            "hooks": {
                "PreCompact": [
                    {
                        "matcher": "",
                        "hooks": [{"type": "command", "command": "save-context.sh"}]
                    }
                ]
            }
        }
        result = check_precompact_hook(settings)
        self.assertTrue(result["has_precompact_hook"])
        self.assertEqual(result["hook_count"], 1)

    def test_settings_with_env_and_precompact(self):
        """Verify audit_settings includes both new fields."""
        settings = {
            "deny": [],
            "allow": [],
            "hooks": {
                "PreCompact": [
                    {"matcher": "", "hooks": [{"type": "command", "command": "save.sh"}]}
                ]
            },
        }
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(settings, f)
        f.close()
        try:
            result = audit_settings(f.name)
            self.assertIn("env_protection", result)
            self.assertIn("precompact_hook", result)
            self.assertTrue(result["precompact_hook"]["has_precompact_hook"])
        finally:
            os.unlink(f.name)


if __name__ == "__main__":
    unittest.main()
