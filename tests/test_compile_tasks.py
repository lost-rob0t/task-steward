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
        for issue, generation in ((1, 2), (26, 1), (28, 2), (30, 2), (32, 2), (34, 2), (36, 2), (38, 2), (40, 2), (42, 2)):
            task = f"task_stward_rage_issue_{issue}"
            self.assertIn(f"task({task}).", first)
            self.assertIn(f"task_state({task}, closed).", first)
            self.assertNotIn(f"task_state({task}, open).", first)
            self.assertIn(f"task_generation({task}, {generation}).", first)
        self.assertIn(
            "task_source(task_stward_rage_issue_42, 'github-issue:lost-rob0t/task-stward-rage#42').",
            first,
        )
        self.assertIn("task_dependency(_, _) :- fail.", first)
        self.assertTrue(first.startswith("% GENERATED FILE. DO NOT EDIT."))

    def test_empty_dependency_relation_is_defined(self) -> None:
        doc = {
            "version": 1,
            "tasks": [
                {
                    "id": "one",
                    "project": "a",
                    "source": "issue:a#1",
                    "state": "open",
                }
            ],
            "observed_by": "task-steward",
            "observed_at": "2026-08-22T00:00:00Z",
        }
        compiled = compile_tasks.compile_tasks(doc)
        self.assertIn("task_dependency(_, _) :- fail.", compiled)

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
