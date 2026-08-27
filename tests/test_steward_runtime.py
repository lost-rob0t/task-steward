from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "steward_runtime", ROOT / "scripts" / "steward_runtime.py"
)
assert SPEC and SPEC.loader
steward_runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(steward_runtime)


class LeaseStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.store = steward_runtime.LeaseStore(Path(self.tmp.name) / "runtime.sqlite3")

    def tearDown(self) -> None:
        self.store.close()
        self.tmp.cleanup()

    def test_new_generation_fences_stale_worker_receipt(self) -> None:
        first = self.store.acquire(
            worker="worker-a",
            project="starintel_server",
            task_ref="issue_1",
            ttl_seconds=10,
            now=100.0,
        )
        self.assertEqual(first.generation, 1)

        second = self.store.acquire(
            worker="worker-b",
            project="starintel_server",
            task_ref="issue_1",
            ttl_seconds=10,
            now=111.0,
        )
        self.assertEqual(second.generation, 2)

        with self.assertRaises(steward_runtime.StaleLease):
            self.store.record_receipt(
                worker=first.worker,
                project=first.project,
                task_ref=first.task_ref,
                generation=first.generation,
                lease_token=first.lease_token,
                kind="complete",
                detail="old worker woke up",
                ttl_seconds=10,
                now=112.0,
            )

        receipt = self.store.record_receipt(
            worker=second.worker,
            project=second.project,
            task_ref=second.task_ref,
            generation=second.generation,
            lease_token=second.lease_token,
            kind="heartbeat",
            detail="alive",
            ttl_seconds=10,
            now=112.0,
        )
        self.assertEqual(receipt["status"], "active")

    def test_active_lease_blocks_other_worker_until_expiry(self) -> None:
        self.store.acquire(
            worker="worker-a",
            project="zara",
            task_ref="issue_2",
            ttl_seconds=30,
            now=100.0,
        )
        with self.assertRaises(steward_runtime.LeaseConflict):
            self.store.acquire(
                worker="worker-b",
                project="zara",
                task_ref="issue_2",
                ttl_seconds=30,
                now=120.0,
            )

    def test_receipt_token_is_required(self) -> None:
        lease = self.store.acquire(
            worker="worker-a",
            project="zara",
            task_ref="issue_2",
            ttl_seconds=30,
            now=100.0,
        )
        with self.assertRaises(steward_runtime.InvalidLeaseToken):
            self.store.record_receipt(
                worker=lease.worker,
                project=lease.project,
                task_ref=lease.task_ref,
                generation=lease.generation,
                lease_token="wrong-token",
                kind="heartbeat",
                detail=None,
                ttl_seconds=30,
                now=101.0,
            )


class _CaptureHandler(BaseHTTPRequestHandler):
    requests: list[dict[str, object]] = []
    status_code = 200

    def do_POST(self) -> None:  # noqa: N802 - stdlib callback name
        length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(length)
        self.__class__.requests.append(
            {
                "path": self.path,
                "headers": dict(self.headers.items()),
                "body": json.loads(payload.decode("utf-8")),
            }
        )
        body = json.dumps({"ok": self.__class__.status_code < 400}).encode("utf-8")
        self.send_response(self.__class__.status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        return


class AgentZeroAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        _CaptureHandler.requests = []
        _CaptureHandler.status_code = 200
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _CaptureHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def _assignment(self) -> steward_runtime.Assignment:
        return steward_runtime.Assignment(
            worker="a0_starintel_server_1",
            project="starintel_server",
            task_ref="pr_102",
            generation=7,
            lease_token="lease-secret",
            score=395,
            source="github-pr:lost-rob0t/starintel-server#102",
            snapshot="fresh",
        )

    def test_dispatch_uses_project_scoped_a2a_without_leaking_token(self) -> None:
        token = "a0-super-secret"
        config = {
            "base_url_env": "TEST_A0_URL",
            "token_env": "TEST_A0_TOKEN",
            "project": "StarIntelServer",
        }
        with mock.patch.dict(
            os.environ,
            {"TEST_A0_URL": self.base_url, "TEST_A0_TOKEN": token},
            clear=False,
        ):
            result = steward_runtime.AgentZeroA2AAdapter(config).dispatch(
                self._assignment(),
                callback_url="http://127.0.0.1:9777/v1/receipt",
            )

        self.assertEqual(result["status"], 200)
        self.assertNotIn(token, json.dumps(result))
        self.assertEqual(len(_CaptureHandler.requests), 1)
        request = _CaptureHandler.requests[0]
        self.assertEqual(
            request["path"], "/a2a/t-a0-super-secret/p-StarIntelServer"
        )
        message = request["body"]["message"]  # type: ignore[index]
        self.assertIn("pr_102", message)
        self.assertIn("generation: 7", message)
        self.assertIn("lease-secret", message)
        self.assertIn("/v1/receipt", message)

    def test_http_error_is_redacted(self) -> None:
        _CaptureHandler.status_code = 500
        token = "do-not-print-me"
        config = {
            "base_url_env": "TEST_A0_URL",
            "token_env": "TEST_A0_TOKEN",
            "project": "StarIntelServer",
        }
        with mock.patch.dict(
            os.environ,
            {"TEST_A0_URL": self.base_url, "TEST_A0_TOKEN": token},
            clear=False,
        ):
            with self.assertRaises(RuntimeError) as raised:
                steward_runtime.AgentZeroA2AAdapter(config).dispatch(
                    self._assignment(), callback_url=None
                )
        self.assertNotIn(token, str(raised.exception))


if __name__ == "__main__":
    unittest.main()
