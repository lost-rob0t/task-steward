from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location(
    "reconcile_issue_snapshot", SCRIPTS / "reconcile_issue_snapshot.py"
)
assert SPEC and SPEC.loader
reconcile_snapshot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reconcile_snapshot)


class ReconcileIssueSnapshotTests(unittest.TestCase):
    def base_doc(self):
        return {
            "version": 1,
            "tasks": [
                {
                    "id": "task-stward-rage-issue-30",
                    "project": "task-stward-rage",
                    "source": "github-issue:lost-rob0t/task-stward-rage#30",
                    "state": "open",
                    "priority": 10,
                    "generation": 1,
                }
            ],
            "observed_by": "task-steward",
            "observed_at": "2026-08-22T23:50:57Z",
        }

    def test_snapshot_repairs_missed_close_and_adds_open_issue(self):
        payload = [[
            {"number": 30, "state": "closed", "updated_at": "2026-08-23T00:50:26Z"},
            {"number": 32, "state": "open", "updated_at": "2026-08-23T00:52:45Z"},
        ]]
        result = reconcile_snapshot.reconcile_snapshot(self.base_doc(), payload)
        by_id = {row["id"]: row for row in result["tasks"]}
        self.assertEqual(by_id["task-stward-rage-issue-30"]["state"], "closed")
        self.assertEqual(by_id["task-stward-rage-issue-30"]["generation"], 2)
        self.assertEqual(by_id["task-stward-rage-issue-32"]["state"], "open")
        self.assertEqual(by_id["task-stward-rage-issue-32"]["generation"], 1)
        self.assertEqual(result["observed_at"], "2026-08-23T00:52:45Z")

    def test_snapshot_replay_is_idempotent(self):
        payload = [
            {"number": 30, "state": "closed", "updated_at": "2026-08-23T00:50:26Z"}
        ]
        first = reconcile_snapshot.reconcile_snapshot(self.base_doc(), payload)
        second = reconcile_snapshot.reconcile_snapshot(first, payload)
        by_id = {row["id"]: row for row in second["tasks"]}
        self.assertEqual(by_id["task-stward-rage-issue-30"]["generation"], 2)
        self.assertEqual(first, second)

    def test_pull_requests_are_ignored(self):
        payload = [
            {
                "number": 31,
                "state": "closed",
                "updated_at": "2026-08-23T00:50:25Z",
                "pull_request": {"url": "https://example.invalid/pr/31"},
            }
        ]
        result = reconcile_snapshot.reconcile_snapshot(self.base_doc(), payload)
        self.assertEqual(result, self.base_doc())


if __name__ == "__main__":
    unittest.main()
