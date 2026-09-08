from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "compile_managed_github", ROOT / "scripts" / "compile_managed_github.py"
)
assert SPEC and SPEC.loader
compile_managed_github = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(compile_managed_github)
PROJECTS = compile_managed_github.load_yaml(ROOT / "state" / "projects.yml")


def valid_doc() -> dict:
    return {
        "version": 1,
        "observed_by": "task-steward-github",
        "observed_at": "2026-08-23T20:34:00Z",
        "projects": [
            {
                "project": "starintel-server",
                "repo": "lost-rob0t/starintel-server",
                "snapshot": "fresh",
                "observed_at": "2026-08-23T20:34:00Z",
                "work": [
                    {
                        "ref": "pr-105",
                        "kind": "pr",
                        "number": 105,
                        "state": "open",
                        "severity": "high",
                        "readiness": "ready",
                        "ci": "failure",
                        "review": "blocked",
                        "head_sha": "a" * 40,
                        "updated_at": "2026-08-23T20:30:00Z",
                        "source": "github-pr:lost-rob0t/starintel-server#105",
                    }
                ],
            }
        ],
    }


class CompileManagedGithubTests(unittest.TestCase):
    def test_repository_snapshot_compiles_deterministically_with_provenance(self) -> None:
        doc = compile_managed_github.load_yaml(ROOT / "state" / "managed_github.yml")
        first = compile_managed_github.compile_managed(doc, PROJECTS)
        second = compile_managed_github.compile_managed(doc, PROJECTS)
        self.assertEqual(first, second)
        self.assertIn("managed_observed_by(task_steward_github).", first)
        self.assertIn("github_snapshot(starintel_server, 'lost-rob0t/starintel-server', fresh", first)
        self.assertIn("github_work(starintel_server, pr_105).", first)
        self.assertIn("github_work_head_sha(starintel_server, pr_105, '6cba035145d7a4b5b8c35d77a64596e4f3494f3b').", first)
        self.assertIn("github_work_source(starintel_server, pr_105, 'github-pr:lost-rob0t/starintel-server#105').", first)

    def test_unknown_project_is_rejected(self) -> None:
        doc = valid_doc()
        doc["projects"][0]["project"] = "unknown-project"
        with self.assertRaisesRegex(ValueError, "unknown managed project"):
            compile_managed_github.compile_managed(doc, PROJECTS)

    def test_repo_must_match_authored_project_registry(self) -> None:
        doc = valid_doc()
        doc["projects"][0]["repo"] = "evil/other"
        with self.assertRaisesRegex(ValueError, "repo must exactly match"):
            compile_managed_github.compile_managed(doc, PROJECTS)

    def test_task_steward_self_issues_cannot_enter_managed_snapshot(self) -> None:
        doc = valid_doc()
        doc["projects"][0]["project"] = "task-stward-rage"
        doc["projects"][0]["repo"] = "lost-rob0t/task-stward-rage"
        with self.assertRaisesRegex(ValueError, "state/tasks.yml"):
            compile_managed_github.compile_managed(doc, PROJECTS)

    def test_duplicate_work_ref_is_rejected(self) -> None:
        doc = valid_doc()
        doc["projects"][0]["work"].append(copy.deepcopy(doc["projects"][0]["work"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate work ref"):
            compile_managed_github.compile_managed(doc, PROJECTS)

    def test_invalid_severity_is_rejected(self) -> None:
        doc = valid_doc()
        doc["projects"][0]["work"][0]["severity"] = "pwned"
        with self.assertRaisesRegex(ValueError, "invalid severity"):
            compile_managed_github.compile_managed(doc, PROJECTS)

    def test_pr_requires_exact_lowercase_head_sha(self) -> None:
        doc = valid_doc()
        doc["projects"][0]["work"][0]["head_sha"] = "ABC"
        with self.assertRaisesRegex(ValueError, "head_sha"):
            compile_managed_github.compile_managed(doc, PROJECTS)

    def test_source_must_match_kind_repo_and_number(self) -> None:
        doc = valid_doc()
        doc["projects"][0]["work"][0]["source"] = "github-pr:lost-rob0t/zara#105"
        with self.assertRaisesRegex(ValueError, "source must be"):
            compile_managed_github.compile_managed(doc, PROJECTS)

    def test_unbounded_work_snapshot_is_rejected(self) -> None:
        doc = valid_doc()
        item = doc["projects"][0]["work"][0]
        work = []
        for number in range(1, compile_managed_github.MAX_WORK_PER_PROJECT + 2):
            row = copy.deepcopy(item)
            row["number"] = number
            row["ref"] = f"pr-{number}"
            row["source"] = f"github-pr:lost-rob0t/starintel-server#{number}"
            work.append(row)
        doc["projects"][0]["work"] = work
        with self.assertRaisesRegex(ValueError, "at most"):
            compile_managed_github.compile_managed(doc, PROJECTS)

    def test_timestamps_must_be_timezone_aware(self) -> None:
        doc = valid_doc()
        doc["observed_at"] = "2026-08-23T20:34:00"
        with self.assertRaisesRegex(ValueError, "timezone"):
            compile_managed_github.compile_managed(doc, PROJECTS)


if __name__ == "__main__":
    unittest.main()
