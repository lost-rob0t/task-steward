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

        kb, rules, registry = first
        self.assertIn("project(prolog_rlm).", kb)
        self.assertIn("project_mode(task_stward_rage, self_rage_building_experts).", kb)
        self.assertIn("completion_policy(starintel_infra, automated_deployment_ready).", kb)
        self.assertIn("production_ready(prolog_rlm) :-", rules)
        self.assertIn("custom_expert(prolog_rlm_readiness).", registry)
        self.assertIn("custom_expert_stage(prolog_rlm_readiness, completion).", registry)
        self.assertIn("custom_expert_order(prolog_rlm_readiness, 91).", registry)
        self.assertIn("custom_expert_dependency(prolog_rlm_readiness, completion).", registry)
        self.assertTrue(kb.startswith("% GENERATED FILE. DO NOT EDIT."))
        self.assertTrue(rules.startswith("% GENERATED FILE. DO NOT EDIT."))
        self.assertTrue(registry.startswith("% GENERATED FILE. DO NOT EDIT."))

    def test_repository_handoffs_compile_deterministically(self) -> None:
        handoffs = compile_state.load_handoffs(ROOT / "state" / "handoffs.yml")
        first = compile_state.compile_handoffs(handoffs)
        second = compile_state.compile_handoffs(handoffs)
        self.assertEqual(first, second)

        kb, rules = first
        self.assertIn(
            "handoff(infra_to_server, starintel_infra, starintel_server).", kb
        )
        self.assertIn("handoff_status(infra_to_server, armed).", kb)
        self.assertIn(
            "handoff_gate(infra_to_server, automated_deployment_ready).", kb
        )
        self.assertIn(
            "handoff_requirement(infra_to_server, reproducible_builds).", kb
        )
        self.assertIn("handoff_ready(infra_to_server) :-", rules)
        self.assertIn("completion_gate(starintel_infra, automated_deployment_ready, satisfied)", rules)
        self.assertTrue(kb.startswith("% GENERATED FILE. DO NOT EDIT."))
        self.assertTrue(rules.startswith("% GENERATED FILE. DO NOT EDIT."))

    def test_repository_policies_compile_deterministically(self) -> None:
        policies = compile_state.load_policies(ROOT / "state" / "policies.yml")
        first = compile_state.compile_policies(policies)
        second = compile_state.compile_policies(policies)
        self.assertEqual(first, second)

        self.assertIn("policy_version(3).", first)
        self.assertIn("policy_value([user_freeze, active], true).", first)
        self.assertIn(
            "policy_value([user_freeze, steward_self_coding_allowed], true).", first
        )
        self.assertIn(
            "policy_value([user_freeze, explicit_coding_exceptions, task_stward_rage, protected_during_freeze], true).",
            first,
        )
        self.assertIn(
            "policy_value([user_freeze, hard_stops, prolog_rlm, automation_allowed], false).",
            first,
        )
        self.assertIn(
            "policy_value([project_work_order, hourly_auto_dig, primary_queue], investigation_target).",
            first,
        )
        self.assertIn(
            "policy_member([protected_projects], task_stward_rage).", first
        )
        self.assertIn(
            "policy_member([expert_system_deployment, requires], yaml_to_prolog_compiler).",
            first,
        )
        self.assertTrue(first.startswith("% GENERATED FILE. DO NOT EDIT."))

    def test_handoff_inline_rule_is_fail_closed(self) -> None:
        handoffs = [
            {
                "id": "demo-handoff",
                "from": "source",
                "to": "target",
                "status": "armed",
                "completion_gate": "ready",
                "rules": {
                    "allowed_predicates": ["completion_gate/3"],
                    "prolog": "handoff_ready(demo_handoff) :- shell('id').",
                },
            }
        ]
        with self.assertRaisesRegex(ValueError, "non_allowlisted_predicate"):
            compile_state.compile_handoffs(handoffs)

    def test_identifier_normalization_is_stable(self) -> None:
        self.assertEqual(compile_state.prolog_atom("starintel-infra"), "starintel_infra")
        self.assertEqual(compile_state.prolog_atom("Book1"), "book1")
        with self.assertRaises(ValueError):
            compile_state.prolog_atom("../escape")

    def test_inline_directive_is_rejected_before_parse(self) -> None:
        with self.assertRaisesRegex(ValueError, "directives are forbidden"):
            compile_state.validate_inline_prolog(
                ":- initialization(main).", source="test.rules.prolog"
            )

    def test_non_allowlisted_predicate_is_rejected_after_parse(self) -> None:
        with self.assertRaisesRegex(ValueError, "non_allowlisted_predicate"):
            compile_state.validate_inline_prolog(
                "unsafe :- shell('id').", source="test.rules.prolog"
            )

    def test_module_qualified_goal_is_rejected_after_parse(self) -> None:
        with self.assertRaisesRegex(ValueError, "module_qualified_goal"):
            compile_state.validate_inline_prolog(
                "unsafe :- system:foo(bar).", source="test.rules.prolog"
            )

    def test_allowlisted_predicate_and_local_rule_are_accepted(self) -> None:
        text = """
        complete(X) :- observed(X), locally_ok(X).
        locally_ok(X) :- X == ready.
        """
        checked = compile_state.validate_inline_prolog(
            text,
            source="test.rules.prolog",
            allowed_predicates=["observed/1"],
        )
        self.assertIn("complete(X)", checked)
        self.assertIn("locally_ok(X)", checked)

    def test_invalid_predicate_indicator_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid predicate indicator"):
            compile_state.validate_inline_prolog(
                "ok.",
                source="test.rules.prolog",
                allowed_predicates=["../../shell/1"],
            )

    def test_custom_expert_unknown_dependency_is_rejected(self) -> None:
        projects = [
            {
                "id": "demo",
                "repo": "lost-rob0t/demo",
                "status": "active",
                "mode": "rage",
                "experts": [
                    {
                        "name": "demo-check",
                        "stage": "completion",
                        "order": 1,
                        "depends_on": ["ghost"],
                    }
                ],
            }
        ]
        with self.assertRaisesRegex(ValueError, "unknown expert dependencies"):
            compile_state.compile_projects(projects)

    def test_custom_expert_order_collision_is_rejected(self) -> None:
        projects = [
            {
                "id": "demo",
                "repo": "lost-rob0t/demo",
                "status": "active",
                "mode": "rage",
                "experts": [
                    {"name": "first", "stage": "completion", "order": 1},
                    {"name": "second", "stage": "completion", "order": 1},
                ],
            }
        ]
        with self.assertRaisesRegex(ValueError, "same effective order"):
            compile_state.compile_projects(projects)

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
