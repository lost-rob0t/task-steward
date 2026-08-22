from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "compile_deployment", ROOT / "scripts" / "compile_deployment.py"
)
assert SPEC and SPEC.loader
compile_deployment = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(compile_deployment)


class CompileDeploymentTests(unittest.TestCase):
    def test_repository_state_compiles_deterministically(self) -> None:
        doc = compile_deployment.load_deployment(ROOT / "state" / "deployment.yml")
        first = compile_deployment.compile_deployment(doc)
        second = compile_deployment.compile_deployment(doc)
        self.assertEqual(first, second)
        self.assertIn("deployment_declared_state(deployed).", first)
        self.assertIn("deployment_requirement(green_required_ci, satisfied).", first)
        self.assertIn("deployment_requirement(no_p0_p1_deployment_blockers, satisfied).", first)
        self.assertIn("deployment_requirement(yaml_state, satisfied).", first)

    def test_duplicate_requirement_is_rejected(self) -> None:
        doc = {
            "version": 1,
            "state": "building",
            "requirements": [
                {"id": "same", "status": "pending"},
                {"id": "same", "status": "pending"},
            ],
        }
        with self.assertRaisesRegex(ValueError, "duplicate deployment requirement"):
            compile_deployment.compile_deployment(doc)

    def test_satisfied_requirement_requires_evidence(self) -> None:
        doc = {
            "version": 1,
            "state": "building",
            "requirements": [{"id": "gate", "status": "satisfied", "evidence": []}],
        }
        with self.assertRaisesRegex(ValueError, "satisfied status requires evidence"):
            compile_deployment.compile_deployment(doc)

    def test_invalid_status_is_rejected(self) -> None:
        doc = {
            "version": 1,
            "state": "building",
            "requirements": [{"id": "gate", "status": "maybe"}],
        }
        with self.assertRaisesRegex(ValueError, "invalid status"):
            compile_deployment.compile_deployment(doc)


if __name__ == "__main__":
    unittest.main()
