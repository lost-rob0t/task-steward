from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "reconcile_managed_github", ROOT / "scripts" / "reconcile_managed_github.py"
)
assert SPEC and SPEC.loader
reconcile = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reconcile)


class ReconcileManagedGithubTests(unittest.TestCase):
    def test_api_failure_is_unavailable_not_fresh_empty(self) -> None:
        with patch.object(reconcile, "paged_get", side_effect=reconcile.GithubReadError("boom")):
            result = reconcile.snapshot_project(
                "starintel-server",
                "lost-rob0t/starintel-server",
                "token",
                "2026-08-23T20:34:00+00:00",
            )
        self.assertEqual(result["snapshot"], "unavailable")
        self.assertEqual(result["work"], [])

    def test_exact_head_failure_dominates_successful_checks(self) -> None:
        checks = [
            {"status": "completed", "conclusion": "success"},
            {"status": "completed", "conclusion": "failure"},
        ]
        self.assertEqual(reconcile.classify_ci(checks, {"state": "success", "statuses": []}), "failure")

    def test_exact_head_pending_is_not_false_green(self) -> None:
        checks = [{"status": "in_progress", "conclusion": None}]
        self.assertEqual(reconcile.classify_ci(checks, {"state": "pending", "statuses": []}), "pending")

    def test_no_exact_head_checks_is_unknown(self) -> None:
        self.assertEqual(reconcile.classify_ci([], {"state": "", "statuses": []}), "unknown")

    def test_severity_labels_are_deterministic(self) -> None:
        self.assertEqual(reconcile.severity_from_labels({"p0", "bug"}), "critical")
        self.assertEqual(reconcile.severity_from_labels({"p1"}), "high")
        self.assertEqual(reconcile.severity_from_labels({"p3"}), "low")
        self.assertEqual(reconcile.severity_from_labels({"bug"}), "normal")

    def test_blocked_issue_is_not_dependency_ready(self) -> None:
        self.assertEqual(reconcile.issue_readiness({"blocked"}), "blocked")
        self.assertEqual(reconcile.issue_readiness({"bug"}), "ready")

    def test_explicit_followup_issue_becomes_followup_work(self) -> None:
        item = reconcile.issue_work(
            "lost-rob0t/zara",
            {
                "number": 200,
                "labels": [{"name": "post-merge"}],
                "updated_at": "2026-08-23T20:00:00Z",
            },
        )
        self.assertEqual(item["kind"], "followup")
        self.assertEqual(item["source"], "github-followup:lost-rob0t/zara#200")

    def test_graphql_review_surface_is_query_only(self) -> None:
        normalized = " ".join(reconcile.GRAPHQL_REVIEW_QUERY.lower().split())
        self.assertTrue(normalized.startswith("query "))
        self.assertNotIn("mutation", normalized)

    def test_self_repository_is_not_managed_external_input(self) -> None:
        projects = reconcile.load_projects()
        self.assertNotIn(("task-stward-rage", "lost-rob0t/task-stward-rage"), projects)
        self.assertIn(("starintel-server", "lost-rob0t/starintel-server"), projects)


if __name__ == "__main__":
    unittest.main()
