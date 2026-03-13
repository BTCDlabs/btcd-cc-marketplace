#!/usr/bin/env python3
"""Tests for hook_validator.py."""

import os
import stat
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hook_validator import (
    check_shebang,
    check_strict_mode,
    check_unquoted_variables,
    check_file_permissions,
    check_syntax,
    validate_hook_script,
    HookIssue,
)


class TestCheckShebang(unittest.TestCase):
    def test_valid_shebang(self):
        issues = check_shebang("test.sh", ["#!/usr/bin/env bash", "echo hello"])
        self.assertEqual(len(issues), 0)

    def test_missing_shebang(self):
        issues = check_shebang("test.sh", ["echo hello"])
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].category, "shebang")

    def test_empty_file(self):
        issues = check_shebang("test.sh", [])
        self.assertEqual(len(issues), 1)

    def test_python_shebang(self):
        issues = check_shebang("test.py", ["#!/usr/bin/env python3", "import sys"])
        self.assertEqual(len(issues), 0)


class TestCheckStrictMode(unittest.TestCase):
    def test_has_pipefail(self):
        content = "#!/bin/bash\nset -euo pipefail\necho hello"
        lines = content.split("\n")
        issues = check_strict_mode("test.sh", lines, content)
        self.assertEqual(len(issues), 0)

    def test_has_set_e(self):
        content = "#!/bin/bash\nset -e\necho hello"
        lines = content.split("\n")
        issues = check_strict_mode("test.sh", lines, content)
        self.assertEqual(len(issues), 0)

    def test_missing_strict_mode(self):
        content = "#!/bin/bash\necho hello"
        lines = content.split("\n")
        issues = check_strict_mode("test.sh", lines, content)
        self.assertEqual(len(issues), 1)

    def test_non_bash_script(self):
        content = "#!/usr/bin/env python3\nimport sys"
        lines = content.split("\n")
        issues = check_strict_mode("test.py", lines, content)
        self.assertEqual(len(issues), 0)


class TestCheckUnquotedVariables(unittest.TestCase):
    def test_clean_script(self):
        lines = ["#!/bin/bash", 'echo "$VAR"', '# comment $VAR']
        issues = check_unquoted_variables("test.sh", lines)
        self.assertEqual(len(issues), 0)

    def test_unquoted_in_rm(self):
        lines = ["#!/bin/bash", "rm $FILE"]
        issues = check_unquoted_variables("test.sh", lines)
        self.assertGreater(len(issues), 0)

    def test_eval_with_variable(self):
        lines = ["#!/bin/bash", "eval $CMD"]
        issues = check_unquoted_variables("test.sh", lines)
        self.assertGreater(len(issues), 0)


class TestValidateHookScript(unittest.TestCase):
    def _write_script(self, content, executable=True):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False)
        f.write(content)
        f.close()
        if executable:
            os.chmod(f.name, os.stat(f.name).st_mode | stat.S_IEXEC)
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_good_script(self):
        path = self._write_script("#!/usr/bin/env bash\nset -euo pipefail\necho hello\n")
        issues = validate_hook_script(path)
        # Should have no critical/high issues
        critical = [i for i in issues if i.severity in ("critical", "high")]
        self.assertEqual(len(critical), 0)

    def test_missing_script(self):
        issues = validate_hook_script("/nonexistent/script.sh")
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].severity, "critical")

    def test_not_executable(self):
        path = self._write_script("#!/usr/bin/env bash\nset -euo pipefail\n", executable=False)
        issues = validate_hook_script(path)
        perm_issues = [i for i in issues if i.category == "permissions"]
        self.assertGreater(len(perm_issues), 0)

    def test_syntax_error(self):
        path = self._write_script('#!/bin/bash\nset -euo pipefail\nif [[ true; then\n')
        issues = validate_hook_script(path)
        syntax_issues = [i for i in issues if i.category == "syntax"]
        self.assertGreater(len(syntax_issues), 0)


class TestActualHookScripts(unittest.TestCase):
    """Test against actual hook scripts in the repo."""

    def test_validate_repo_hooks(self):
        hooks_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "hooks", "scripts"
        )
        if not os.path.isdir(hooks_dir):
            self.skipTest("Hooks scripts directory not found")

        import glob
        scripts = glob.glob(os.path.join(hooks_dir, "*.sh"))
        self.assertGreater(len(scripts), 0, "No hook scripts found")

        for script in scripts:
            issues = validate_hook_script(script)
            # No critical issues (syntax errors) in our own scripts
            critical = [i for i in issues if i.severity == "critical"]
            self.assertEqual(len(critical), 0, f"Critical issues in {script}: {[i.message for i in critical]}")


if __name__ == "__main__":
    unittest.main()
