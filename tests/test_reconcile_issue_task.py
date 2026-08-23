from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "reconcile_issue_task", ROOT / "scripts" / "reconcile_issue_task.py"
)
reconciler = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(reconciler)


class ReconcileIssueTaskTests(unittest.TestCase):
    def base_doc(self):
        return {
            "version": 1,
            "tasks": [
                {
                    "id": "task-stward-rage-issue-28",
                    "project": "task-stward-rage",
                    "source": "github-issue:lost-rob0t/task-stward-rage#28",
                    "state": "open",
                    "priority": 10,
                    "generation": 1,
                }
            ],
            "observed_by": "task-steward",
            "observed_at": "2026-08-22T22:47:15Z",
        }

    def event(self, number=28, state="closed", updated_at="2026-08-22T23:49:42Z", repo="lost-rob0t/task-stward-rage"):
        return {
            "repository": {"full_name": repo},
            "issue": {
                "number": number,
                "state": state,
                "updated_at": updated_at,
            },
        }

    def test_state_transition_increments_generation(self):
        doc = self.base_doc()
        result = reconciler.reconcile_event(doc, self.event())
        row = result["tasks"][0]
        self.assertEqual(row["state"], "closed")
        self.assertEqual(row["generation"], 2)
        self.assertEqual(result["observed_at"], "2026-08-22T23:49:42Z")

    def test_replay_is_idempotent(self):
        first = reconciler.reconcile_event(self.base_doc(), self.event())
        second = reconciler.reconcile_event(copy.deepcopy(first), self.event())
        self.assertEqual(first, second)
        self.assertEqual(second["tasks"][0]["generation"], 2)

    def test_new_issue_is_added_open_at_generation_one(self):
        result = reconciler.reconcile_event(
            self.base_doc(),
            self.event(number=30, state="open", updated_at="2026-08-22T23:50:57Z"),
        )
        row = next(row for row in result["tasks"] if row["id"] == "task-stward-rage-issue-30")
        self.assertEqual(row["state"], "open")
        self.assertEqual(row["priority"], 10)
        self.assertEqual(row["generation"], 1)

    def test_foreign_repository_event_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "foreign repository"):
            reconciler.reconcile_event(self.base_doc(), self.event(repo="lost-rob0t/zara"))


if __name__ == "__main__":
    unittest.main()
