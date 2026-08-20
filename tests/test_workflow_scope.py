from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_workflow_scope", ROOT / "scripts" / "validate_workflow_scope.py")
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class WorkflowScopeTests(unittest.TestCase):
    def workflow(self, run: str = "echo ok", permissions=None):
        return {
            "on": {"push": {"branches": ["main"]}, "pull_request": {"branches": ["main"]}, "workflow_dispatch": {}},
            "permissions": permissions if permissions is not None else {"contents": "read"},
            "jobs": {"validate": {"steps": [{"uses": "actions/checkout@v4"}, {"run": run}]}},
        }

    def test_current_workflow_passes(self):
        validator.validate(ROOT / ".github" / "workflows" / "steward.yml")

    def test_write_permission_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "permissions"):
            validator.validate_permissions(Path("bad.yml"), self.workflow(permissions={"contents": "write"}))

    def test_external_git_push_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "git push"):
            validator.validate_steps(Path("bad.yml"), self.workflow(run="git push origin main"))

    def test_arbitrary_action_is_rejected(self):
        workflow = self.workflow()
        workflow["jobs"]["validate"]["steps"][0]["uses"] = "third-party/deploy@v1"
        with self.assertRaisesRegex(ValueError, "non-allow-listed action"):
            validator.validate_steps(Path("bad.yml"), workflow)

    def test_unbounded_push_branch_is_rejected(self):
        workflow = self.workflow()
        workflow["on"]["push"]["branches"] = ["*"]
        with self.assertRaisesRegex(ValueError, "bounded to main"):
            validator.validate_triggers(Path("bad.yml"), workflow)


if __name__ == "__main__":
    unittest.main()
