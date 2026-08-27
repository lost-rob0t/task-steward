from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "compile_workers", ROOT / "scripts" / "compile_workers.py"
)
assert SPEC and SPEC.loader
compile_workers = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(compile_workers)


class CompileWorkersTests(unittest.TestCase):
    def test_repository_workers_compile_deterministically(self) -> None:
        workers = compile_workers.load_workers(ROOT / "state" / "workers.yml")
        first = compile_workers.compile_workers(workers)
        second = compile_workers.compile_workers(workers)
        self.assertEqual(first, second)
        self.assertIn("worker(a0_starintel_server_1).", first)
        self.assertIn(
            "worker_project(a0_starintel_server_1, starintel_server).", first
        )
        self.assertIn(
            "worker_backend(a0_starintel_server_1, agent_zero_a2a).", first
        )
        self.assertIn("worker_enabled(a0_starintel_server_1).", first)
        self.assertIn(
            "worker_config(a0_starintel_server_1, token_env, 'STEWARD_A0_STARINTEL_TOKEN').",
            first,
        )
        self.assertNotIn("actual-token", first)
        self.assertTrue(first.startswith("% GENERATED FILE. DO NOT EDIT."))

    def test_secret_values_are_rejected(self) -> None:
        workers = [
            {
                "id": "demo",
                "project": "starintel-server",
                "backend": "agent-zero-a2a",
                "enabled": True,
                "config": {
                    "base_url_env": "A0_URL",
                    "token_env": "A0_TOKEN",
                    "project": "Demo",
                    "token": "actual-token",
                },
            }
        ]
        with self.assertRaisesRegex(ValueError, "secret-bearing key"):
            compile_workers.compile_workers(workers)

    def test_embedded_a2a_token_is_rejected(self) -> None:
        workers = [
            {
                "id": "demo",
                "project": "starintel-server",
                "backend": "agent-zero-a2a",
                "enabled": True,
                "config": {
                    "base_url_env": "A0_URL",
                    "token_env": "A0_TOKEN",
                    "project": "Demo",
                    "note": "http://agent/a2a/t-actual-token/p-Demo",
                },
            }
        ]
        with self.assertRaisesRegex(ValueError, "embedded Agent Zero token"):
            compile_workers.compile_workers(workers)

    def test_agent_zero_requires_environment_indirection(self) -> None:
        workers = [
            {
                "id": "demo",
                "project": "starintel-server",
                "backend": "agent-zero-a2a",
                "enabled": True,
                "config": {"project": "Demo"},
            }
        ]
        with self.assertRaisesRegex(ValueError, "base_url_env"):
            compile_workers.compile_workers(workers)

    def test_duplicate_worker_id_is_rejected(self) -> None:
        worker = {
            "id": "demo",
            "project": "starintel-server",
            "backend": "agent-zero-a2a",
            "enabled": True,
            "config": {
                "base_url_env": "A0_URL",
                "token_env": "A0_TOKEN",
                "project": "Demo",
            },
        }
        with self.assertRaisesRegex(ValueError, "duplicate worker id"):
            compile_workers.compile_workers([worker, dict(worker)])

    def test_load_rejects_wrong_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workers.yml"
            path.write_text("version: 2\nworkers: []\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "expected version: 1"):
                compile_workers.load_workers(path)


if __name__ == "__main__":
    unittest.main()
