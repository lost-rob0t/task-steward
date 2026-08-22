from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "compile_tasks", ROOT / "scripts" / "compile_tasks.py"
)
assert SPEC and SPEC.loader
compile_tasks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(compile_tasks)


class CompileTasksTests(unittest.TestCase):
    def test_repository_tasks_compile_deterministically(self) -> None:
        doc = compile_tasks.load_tasks(ROOT / "state" / "tasks.yml")
        first = compile_tasks.compile_tasks(doc)
        second = compile_tasks.compile_tasks(doc)
        self.assertEqual(first, second)
        self.assertIn("task(task_stward_rage_issue_1).", first)
        self.assertIn(
            "task_source(task_stward_rage_issue_1, 'github-issue:lost-rob0t/task-stward-rage#1').",
            first,
        )
        self.assertIn("task_state(task_stward_rage_issue_1, closed).", first)
        self.assertNotIn("task_state(task_stward_rage_issue_1, open).", first)
        self.assertIn("task_generation(task_stward_rage_issue_1, 2).", first)
        self.assertTrue(first.startswith("% GENERATED FILE. DO NOT EDIT."))

    def test_duplicate_task_ids_are_rejected(self) -> None:
        doc = {
            "version": 1,
            "tasks": [
                {"id": "same", "project": "a", "source": "issue:a#1", "state": "open"},
                {"id": "same", "project": "a", "source": "issue:a#2", "state": "open"},
            ],
            "observed_by": "task-steward",
            "observed_at": "2026-08-22T00:00:00Z",
        }
        with self.assertRaisesRegex(ValueError, "duplicate task id"):
            compile_tasks.compile_tasks(doc)

    def test_duplicate_canonical_sources_are_rejected(self) -> None:
        doc = {
            "version": 1,
            "tasks": [
                {"id": "one", "project": "a", "source": "issue:a#1", "state": "open"},
                {"id": "two", "project": "a", "source": "issue:a#1", "state": "open"},
            ],
            "observed_by": "task-steward",
            "observed_at": "2026-08-22T00:00:00Z",
        }
        with self.assertRaisesRegex(ValueError, "duplicate task source"):
            compile_tasks.compile_tasks(doc)

    def test_unknown_dependency_is_rejected(self) -> None:
        doc = {
            "version": 1,
            "tasks": [
                {
                    "id": "one",
                    "project": "a",
                    "source": "issue:a#1",
                    "state": "open",
                    "dependencies": ["missing"],
                }
            ],
            "observed_by": "task-steward",
            "observed_at": "2026-08-22T00:00:00Z",
        }
        with self.assertRaisesRegex(ValueError, "unknown dependencies"):
            compile_tasks.compile_tasks(doc)


if __name__ == "__main__":
    unittest.main()
