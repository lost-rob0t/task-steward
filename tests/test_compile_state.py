from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "compile_state", ROOT / "scripts" / "compile_state.py"
)
assert SPEC and SPEC.loader
compile_state = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(compile_state)


class CompileStateTests(unittest.TestCase):
    def test_repository_projects_compile_deterministically(self) -> None:
        projects = compile_state.load_projects(ROOT / "state" / "projects.yml")
        first = compile_state.compile_projects(projects)
        second = compile_state.compile_projects(projects)
        self.assertEqual(first, second)

        kb, rules = first
        self.assertIn("project(prolog_rlm).", kb)
        self.assertIn("project_mode(task_stward_rage, self_rage_building_experts).", kb)
        self.assertIn("completion_policy(starintel_infra, automated_deployment_ready).", kb)
        self.assertIn("production_ready(prolog_rlm) :-", rules)
        self.assertTrue(kb.startswith("% GENERATED FILE. DO NOT EDIT."))
        self.assertTrue(rules.startswith("% GENERATED FILE. DO NOT EDIT."))

    def test_identifier_normalization_is_stable(self) -> None:
        self.assertEqual(compile_state.prolog_atom("starintel-infra"), "starintel_infra")
        self.assertEqual(compile_state.prolog_atom("Book1"), "book1")
        with self.assertRaises(ValueError):
            compile_state.prolog_atom("../escape")

    def test_inline_directive_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "directives are forbidden"):
            compile_state.validate_inline_prolog(
                ":- initialization(main).", source="test.rules.prolog"
            )

    def test_inline_shell_and_module_escape_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "forbidden predicate shell"):
            compile_state.validate_inline_prolog(
                "unsafe :- shell('id').", source="test.rules.prolog"
            )
        with self.assertRaisesRegex(ValueError, "module-qualified calls are forbidden"):
            compile_state.validate_inline_prolog(
                "unsafe :- system:foo(bar).", source="test.rules.prolog"
            )

    def test_check_mode_detects_stale_generated_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "generated.pl"
            path.write_text("stale\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                compile_state.write_or_check(path, "fresh\n", check=True)

    def test_write_then_check_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "generated.pl"
            compile_state.write_or_check(path, "stable\n", check=False)
            compile_state.write_or_check(path, "stable\n", check=True)
            self.assertEqual(path.read_text(encoding="utf-8"), "stable\n")


if __name__ == "__main__":
    unittest.main()
