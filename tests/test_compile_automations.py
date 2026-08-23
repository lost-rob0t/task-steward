from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "compile_automations", ROOT / "scripts" / "compile_automations.py"
)
assert SPEC and SPEC.loader
compile_automations = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(compile_automations)


class CompileAutomationsTests(unittest.TestCase):
    def test_repository_automations_compile_deterministically(self) -> None:
        doc = compile_automations.load_automations(ROOT / "state" / "automations.yml")
        first = compile_automations.compile_automations(doc)
        second = compile_automations.compile_automations(doc)
        self.assertEqual(first, second)

        self.assertIn("automation('6a54903dc26081918683fbdbc2c6c7cd').", first)
        self.assertIn(
            "automation_state('6a54903dc26081918683fbdbc2c6c7cd', active).", first
        )
        self.assertIn(
            "automation_project('6a54903dc26081918683fbdbc2c6c7cd', task_stward_rage).",
            first,
        )
        self.assertIn(
            "automation_mode('6a54903dc26081918683fbdbc2c6c7cd', deployed_scheduling_self_rage_fallback).",
            first,
        )
        self.assertNotIn("reconciliation_plus_self_rage", first)
        self.assertIn(
            "automation_state('6a8649dc3f708191b51269995b51700a', paused).", first
        )
        self.assertIn(
            "automation_state('6a864c35bce48191883144c38781b20e', active).", first
        )
        self.assertIn(
            "automation_project('6a864c35bce48191883144c38781b20e', starintel_server).", first
        )
        self.assertIn(
            "automation_state('6a8934a82ef881919ab153b6aec87c15', paused).", first
        )
        self.assertNotIn(
            "automation_state('6a8934a82ef881919ab153b6aec87c15', active).", first
        )
        self.assertIn("reconciliation_value([active_task_count], 5).", first)
        self.assertIn("reconciliation_value([coding_freeze], lifted).", first)
        self.assertIn("reconciliation_value([prolog_rlm_workers_enabled], false).", first)
        self.assertIn("reconciliation_value([local_recall_worker_enabled], false).", first)
        self.assertIn("reconciliation_value([starintel_server_worker_enabled], true).", first)
        self.assertIn(
            "reconciliation_value([starintel_server_primary_coding_priority], true).", first
        )
        self.assertNotIn("coding_freeze_exception_workers", first)
        self.assertIn("observed_by(task_steward).", first)
        self.assertIn("observed_at('2026-08-23T03:52:16+00:00').", first)
        self.assertTrue(first.startswith("% GENERATED FILE. DO NOT EDIT."))

    def test_declared_active_count_must_match_active_entries(self) -> None:
        doc = {
            "version": 1,
            "active": [
                {"id": "worker-a", "title": "A", "project": "zara"},
                {"id": "worker-b", "title": "B", "project": "local-recall"},
            ],
            "paused": [],
            "observed_by": "task-steward",
            "observed_at": "2026-08-22T00:00:00Z",
            "reconciliation": {"active_task_count": 1},
        }
        with self.assertRaisesRegex(ValueError, "active_task_count"):
            compile_automations.compile_automations(doc)

    def test_duplicate_id_across_active_and_paused_is_rejected(self) -> None:
        doc = {
            "version": 1,
            "active": [{"id": "same-id", "title": "A", "project": "zara"}],
            "paused": [{"id": "same-id", "title": "B", "project": "zara"}],
            "observed_by": "task-steward",
            "observed_at": "2026-08-22T00:00:00Z",
            "reconciliation": {"active_task_count": 1},
        }
        with self.assertRaisesRegex(ValueError, "duplicate automation id"):
            compile_automations.compile_automations(doc)


if __name__ == "__main__":
    unittest.main()
