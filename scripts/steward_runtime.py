#!/usr/bin/env python3
"""Standalone runtime for Prolog-authorized Task Steward workers.

The runtime never chooses work. It asks the canonical Prolog export for the
current managed decision, fences ownership in SQLite, and dispatches only that
assignment through a configured backend.
"""
from __future__ import annotations

import argparse
import hmac
import ipaddress
import json
import os
import queue
import re
import secrets
import sqlite3
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, NamedTuple

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKERS = ROOT / "state" / "workers.yml"
DEFAULT_DB = ROOT / "state" / "generated" / "runtime.sqlite3"
ATOM_RE = re.compile(r"^[a-z][a-z0-9_]*$")
TERMINAL_RECEIPTS = frozenset({"complete", "blocked", "yield"})
LIVE_RECEIPTS = frozenset({"heartbeat", "status"})
RECEIPT_KINDS = TERMINAL_RECEIPTS | LIVE_RECEIPTS


class RuntimeErrorBase(Exception):
    pass


class SchedulerError(RuntimeErrorBase):
    pass


class NoAssignment(RuntimeErrorBase):
    pass


class WorkerNotEligible(RuntimeErrorBase):
    pass


class LeaseConflict(RuntimeErrorBase):
    pass


class StaleLease(RuntimeErrorBase):
    pass


class InvalidLeaseToken(RuntimeErrorBase):
    pass


class WorkerSpec(NamedTuple):
    worker: str
    project: str
    backend: str
    enabled: bool
    config: dict[str, str]


class Lease(NamedTuple):
    worker: str
    project: str
    task_ref: str
    generation: int
    lease_token: str
    expires_at: float


class Assignment(NamedTuple):
    worker: str
    project: str
    task_ref: str
    generation: int
    lease_token: str
    score: int
    source: str
    snapshot: str

    def public_dict(self) -> dict[str, Any]:
        return self._asdict()


def steward_atom(value: str) -> str:
    atom = value.strip().lower().replace("-", "_")
    if not ATOM_RE.fullmatch(atom):
        raise ValueError(f"invalid steward identifier: {value!r}")
    return atom


def load_worker_specs(path: Path = DEFAULT_WORKERS) -> dict[str, WorkerSpec]:
    with path.open("r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    if not isinstance(doc, dict) or doc.get("version") != 1:
        raise ValueError(f"{path}: expected version: 1")
    raw_workers = doc.get("workers")
    if not isinstance(raw_workers, list):
        raise ValueError(f"{path}: workers must be a list")

    specs: dict[str, WorkerSpec] = {}
    for raw in raw_workers:
        if not isinstance(raw, dict):
            raise ValueError("worker entry must be a mapping")
        worker = raw.get("id")
        project = raw.get("project")
        backend = raw.get("backend")
        enabled = raw.get("enabled")
        config = raw.get("config") or {}
        if not all(isinstance(v, str) and v for v in (worker, project, backend)):
            raise ValueError("worker id/project/backend must be non-empty strings")
        if enabled not in (True, False):
            raise ValueError(f"{worker}: enabled must be boolean")
        if not isinstance(config, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in config.items()
        ):
            raise ValueError(f"{worker}: config must contain string keys and values")
        key = steward_atom(worker)
        if key in specs:
            raise ValueError(f"duplicate worker id: {worker}")
        specs[key] = WorkerSpec(
            worker=key,
            project=steward_atom(project),
            backend=steward_atom(backend),
            enabled=bool(enabled),
            config=dict(config),
        )
    return specs


class PrologScheduler:
    def __init__(self, root: Path = ROOT) -> None:
        self.root = root

    def decisions(self) -> dict[str, Any]:
        proc = subprocess.run(
            [
                "swipl",
                "-q",
                "-s",
                "scripts/export_managed_decisions.pl",
                "-g",
                "main",
                "-t",
                "halt",
            ],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            raise SchedulerError("Prolog managed decision export failed")
        try:
            decision = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            raise SchedulerError("Prolog managed decision export was not valid JSON") from exc
        if decision.get("authority") != "prolog":
            raise SchedulerError("managed decision authority is not Prolog")
        return decision

    def worker_dispatchable(self, worker: str, project: str) -> bool:
        worker_atom = steward_atom(worker)
        project_atom = steward_atom(project)
        goal = (
            f"(steward_worker_dispatchable({worker_atom},{project_atom},_)"
            "->halt(0);halt(3))"
        )
        proc = subprocess.run(
            ["swipl", "-q", "-s", "steward.pl", "-g", goal],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode == 0:
            return True
        if proc.returncode == 3:
            return False
        raise SchedulerError("Prolog worker dispatchability query failed")


class LeaseStore:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        conn = self._connect()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS leases (
                    project TEXT NOT NULL,
                    task_ref TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    worker TEXT NOT NULL,
                    lease_token TEXT NOT NULL,
                    expires_at REAL NOT NULL,
                    status TEXT NOT NULL,
                    updated_at REAL NOT NULL,
                    PRIMARY KEY (project, task_ref)
                );
                CREATE TABLE IF NOT EXISTS receipts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project TEXT NOT NULL,
                    task_ref TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    worker TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    detail TEXT,
                    observed_at REAL NOT NULL
                );
                """
            )
        finally:
            conn.close()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=FULL")
        return conn

    def close(self) -> None:
        """Per-operation connections need no persistent close action."""

    def acquire(
        self,
        *,
        worker: str,
        project: str,
        task_ref: str,
        ttl_seconds: int,
        now: float | None = None,
    ) -> Lease:
        observed = time.time() if now is None else now
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT generation, worker, lease_token, expires_at, status "
                "FROM leases WHERE project = ? AND task_ref = ?",
                (project, task_ref),
            ).fetchone()
            if row is not None and row["status"] == "active" and row["expires_at"] > observed:
                if row["worker"] != worker:
                    raise LeaseConflict(
                        f"{project}/{task_ref} is leased by another worker"
                    )
                lease = Lease(
                    worker=worker,
                    project=project,
                    task_ref=task_ref,
                    generation=int(row["generation"]),
                    lease_token=str(row["lease_token"]),
                    expires_at=float(row["expires_at"]),
                )
                conn.commit()
                return lease

            generation = 1 if row is None else int(row["generation"]) + 1
            token = secrets.token_urlsafe(24)
            expires_at = observed + ttl_seconds
            conn.execute(
                "INSERT INTO leases(project, task_ref, generation, worker, lease_token, "
                "expires_at, status, updated_at) VALUES (?, ?, ?, ?, ?, ?, 'active', ?) "
                "ON CONFLICT(project, task_ref) DO UPDATE SET "
                "generation=excluded.generation, worker=excluded.worker, "
                "lease_token=excluded.lease_token, expires_at=excluded.expires_at, "
                "status='active', updated_at=excluded.updated_at",
                (project, task_ref, generation, worker, token, expires_at, observed),
            )
            conn.commit()
            return Lease(worker, project, task_ref, generation, token, expires_at)
        except Exception:
            if conn.in_transaction:
                conn.rollback()
            raise
        finally:
            conn.close()

    def record_receipt(
        self,
        *,
        worker: str,
        project: str,
        task_ref: str,
        generation: int,
        lease_token: str,
        kind: str,
        detail: str | None,
        ttl_seconds: int,
        now: float | None = None,
    ) -> dict[str, Any]:
        if kind not in RECEIPT_KINDS:
            raise ValueError(f"unsupported receipt kind: {kind}")
        observed = time.time() if now is None else now
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT generation, worker, lease_token, expires_at, status "
                "FROM leases WHERE project = ? AND task_ref = ?",
                (project, task_ref),
            ).fetchone()
            if row is None or int(row["generation"]) != generation or row["worker"] != worker:
                raise StaleLease(f"stale lease generation for {project}/{task_ref}")
            if not hmac.compare_digest(str(row["lease_token"]), lease_token):
                raise InvalidLeaseToken("lease token does not match current generation")
            if row["status"] != "active":
                if row["status"] == kind:
                    conn.commit()
                    return {"status": kind, "generation": generation, "idempotent": True}
                raise StaleLease(f"lease is already terminal: {row['status']}")
            if float(row["expires_at"]) <= observed:
                conn.execute(
                    "UPDATE leases SET status='expired', updated_at=? "
                    "WHERE project=? AND task_ref=?",
                    (observed, project, task_ref),
                )
                conn.commit()
                raise StaleLease(f"lease expired for {project}/{task_ref}")

            status = "active" if kind in LIVE_RECEIPTS else kind
            expires_at = observed + ttl_seconds if kind in LIVE_RECEIPTS else float(row["expires_at"])
            conn.execute(
                "UPDATE leases SET status=?, expires_at=?, updated_at=? "
                "WHERE project=? AND task_ref=?",
                (status, expires_at, observed, project, task_ref),
            )
            conn.execute(
                "INSERT INTO receipts(project, task_ref, generation, worker, kind, detail, observed_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (project, task_ref, generation, worker, kind, detail, observed),
            )
            conn.commit()
            return {"status": status, "generation": generation, "expires_at": expires_at}
        except Exception:
            if conn.in_transaction:
                conn.rollback()
            raise
        finally:
            conn.close()

    def active(self, *, now: float | None = None) -> list[dict[str, Any]]:
        observed = time.time() if now is None else now
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT project, task_ref, generation, worker, expires_at, status "
                "FROM leases WHERE status='active' AND expires_at > ? ORDER BY project, task_ref",
                (observed,),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()


def assignment_prompt(assignment: Assignment, callback_url: str | None) -> str:
    callback = callback_url or "<no callback URL supplied>"
    return f"""TASK STEWARD ASSIGNMENT\n\nExecute only the Prolog-authorized assignment below. Do not choose a substitute task.\n\nworker: {assignment.worker}\nproject: {assignment.project}\ntask_ref: {assignment.task_ref}\ngeneration: {assignment.generation}\nlease_token: {assignment.lease_token}\nsource: {assignment.source}\nsnapshot: {assignment.snapshot}\nreceipt_url: {callback}\n\nLoad the task-steward-worker skill and the repository's RAGE skill before work.\nRecover an existing transaction for this exact task before creating a replacement.\nSend heartbeat/status receipts while working and complete/blocked/yield at a transaction boundary.\nEvery receipt must preserve worker, project, task_ref, generation, and lease_token exactly.\nA stale/revoked lease means stop writing immediately and yield.\n"""


class AgentZeroA2AAdapter:
    def __init__(self, config: dict[str, str]) -> None:
        self.config = config

    def dispatch(self, assignment: Assignment, callback_url: str | None) -> dict[str, Any]:
        base_env = self.config.get("base_url_env")
        token_env = self.config.get("token_env")
        project = self.config.get("project")
        if not base_env or not token_env or not project:
            raise RuntimeError("Agent Zero worker config is incomplete")
        base = os.environ.get(base_env)
        token = os.environ.get(token_env)
        if not base or not token:
            raise RuntimeError("Agent Zero endpoint environment is not configured")

        url = (
            base.rstrip("/")
            + "/a2a/t-"
            + urllib.parse.quote(token, safe="")
            + "/p-"
            + urllib.parse.quote(project, safe="")
        )
        body = json.dumps(
            {"message": assignment_prompt(assignment, callback_url)},
            separators=(",", ":"),
        ).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                response.read()
                status = response.status
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"Agent Zero A2A dispatch failed with HTTP {exc.code}") from None
        except urllib.error.URLError:
            raise RuntimeError("Agent Zero A2A dispatch failed to connect") from None
        return {"backend": "agent-zero-a2a", "status": status}


class OpenCodeRunAdapter:
    def __init__(self, config: dict[str, str]) -> None:
        self.config = config

    def dispatch(self, assignment: Assignment, callback_url: str | None) -> dict[str, Any]:
        binary_env = self.config.get("binary_env")
        workdir_env = self.config.get("workdir_env")
        if not binary_env or not workdir_env:
            raise RuntimeError("OpenCode worker config is incomplete")
        binary = os.environ.get(binary_env)
        workdir = os.environ.get(workdir_env)
        if not binary or not workdir:
            raise RuntimeError("OpenCode worker environment is not configured")
        cwd = Path(workdir).expanduser().resolve()
        if not cwd.is_dir():
            raise RuntimeError("OpenCode worker directory does not exist")

        argv = [binary, "run", "--dir", str(cwd)]
        agent = self.config.get("agent")
        if agent:
            argv.extend(["--agent", agent])
        model = self.config.get("model")
        if model:
            argv.extend(["--model", model])
        argv.append(assignment_prompt(assignment, callback_url))
        proc = subprocess.Popen(
            argv,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True,
        )
        return {"backend": "opencode-run", "pid": proc.pid}


class StewardRuntime:
    def __init__(
        self,
        *,
        root: Path = ROOT,
        workers_path: Path = DEFAULT_WORKERS,
        db_path: Path = DEFAULT_DB,
        ttl_seconds: int = 3600,
    ) -> None:
        self.root = root
        self.specs = load_worker_specs(workers_path)
        self.scheduler = PrologScheduler(root)
        self.store = LeaseStore(db_path)
        self.ttl_seconds = ttl_seconds

    def close(self) -> None:
        self.store.close()

    def assignment(self, worker: str) -> Assignment:
        wid = steward_atom(worker)
        spec = self.specs.get(wid)
        if spec is None:
            raise WorkerNotEligible(f"unknown worker: {worker}")
        if not spec.enabled:
            raise WorkerNotEligible(f"worker is disabled: {worker}")

        decisions = self.scheduler.decisions()
        selected = decisions.get("next_external")
        if not isinstance(selected, dict):
            raise NoAssignment("Prolog selected no external work")
        project = steward_atom(str(selected.get("project", "")))
        task_ref = steward_atom(str(selected.get("ref", "")))
        if spec.project != project:
            raise NoAssignment(
                f"current Prolog assignment is for {project}, not worker project {spec.project}"
            )
        if not self.scheduler.worker_dispatchable(wid, project):
            raise WorkerNotEligible(f"Prolog does not permit {wid} to dispatch {project}")

        lease = self.store.acquire(
            worker=wid,
            project=project,
            task_ref=task_ref,
            ttl_seconds=self.ttl_seconds,
        )
        return Assignment(
            worker=wid,
            project=project,
            task_ref=task_ref,
            generation=lease.generation,
            lease_token=lease.lease_token,
            score=int(selected.get("score", 0)),
            source=str(selected.get("source", "")),
            snapshot=str(selected.get("snapshot", "unknown")),
        )

    def receipt(self, payload: dict[str, Any]) -> dict[str, Any]:
        required = ("worker", "project", "task_ref", "generation", "lease_token", "kind")
        if any(key not in payload for key in required):
            raise ValueError("receipt is missing required fields")
        worker = steward_atom(str(payload["worker"]))
        project = steward_atom(str(payload["project"]))
        task_ref = steward_atom(str(payload["task_ref"]))
        generation = int(payload["generation"])
        lease_token = str(payload["lease_token"])
        kind = str(payload["kind"])
        detail = payload.get("detail")
        if detail is not None:
            detail = str(detail)[:4096]

        spec = self.specs.get(worker)
        if spec is None or spec.project != project:
            raise WorkerNotEligible("receipt worker/project is not registered")

        if kind in LIVE_RECEIPTS and not self.scheduler.worker_dispatchable(worker, project):
            result = self.store.record_receipt(
                worker=worker,
                project=project,
                task_ref=task_ref,
                generation=generation,
                lease_token=lease_token,
                kind="yield",
                detail="revoked_by_prolog_policy",
                ttl_seconds=self.ttl_seconds,
            )
            result["revoked"] = True
            return result

        return self.store.record_receipt(
            worker=worker,
            project=project,
            task_ref=task_ref,
            generation=generation,
            lease_token=lease_token,
            kind=kind,
            detail=detail,
            ttl_seconds=self.ttl_seconds,
        )

    def dispatch(self, worker: str, callback_url: str | None) -> dict[str, Any]:
        assignment = self.assignment(worker)
        spec = self.specs[assignment.worker]
        if spec.backend == "agent_zero_a2a":
            adapter: Any = AgentZeroA2AAdapter(spec.config)
        elif spec.backend == "opencode_run":
            adapter = OpenCodeRunAdapter(spec.config)
        else:
            raise WorkerNotEligible(f"backend requires pull/operator mode: {spec.backend}")
        try:
            dispatched = adapter.dispatch(assignment, callback_url)
        except Exception:
            self.store.record_receipt(
                worker=assignment.worker,
                project=assignment.project,
                task_ref=assignment.task_ref,
                generation=assignment.generation,
                lease_token=assignment.lease_token,
                kind="yield",
                detail="dispatch_failed",
                ttl_seconds=self.ttl_seconds,
            )
            raise
        return {"assignment": assignment.public_dict(), "dispatch": dispatched}

    def status(self) -> dict[str, Any]:
        decisions = self.scheduler.decisions()
        workers = [
            {
                "worker": spec.worker,
                "project": spec.project,
                "backend": spec.backend,
                "enabled": spec.enabled,
            }
            for spec in sorted(self.specs.values(), key=lambda item: item.worker)
        ]
        return {
            "authority": "prolog",
            "next_external": decisions.get("next_external"),
            "workers": workers,
            "active_leases": self.store.active(),
        }


class _ActorRequest(NamedTuple):
    method: str
    kwargs: dict[str, Any]
    reply: queue.Queue[Any]


class RuntimeActor:
    """Single-owner actor for runtime state transitions."""

    def __init__(self, factory: Callable[[], StewardRuntime]) -> None:
        self.mailbox: queue.Queue[_ActorRequest | None] = queue.Queue()
        self.factory = factory
        self.thread = threading.Thread(target=self._loop, daemon=True, name="task-steward-runtime")
        self.thread.start()

    def _loop(self) -> None:
        runtime = self.factory()
        try:
            while True:
                request = self.mailbox.get()
                if request is None:
                    return
                try:
                    result = getattr(runtime, request.method)(**request.kwargs)
                except BaseException as exc:
                    request.reply.put((False, exc))
                else:
                    request.reply.put((True, result))
        finally:
            runtime.close()

    def call(self, method: str, **kwargs: Any) -> Any:
        reply: queue.Queue[Any] = queue.Queue(maxsize=1)
        self.mailbox.put(_ActorRequest(method, kwargs, reply))
        ok, value = reply.get()
        if ok:
            return value
        raise value

    def close(self) -> None:
        self.mailbox.put(None)
        self.thread.join(timeout=5)


def _is_loopback(host: str) -> bool:
    if host in {"localhost", "ip6-localhost"}:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def make_handler(
    actor: RuntimeActor,
    *,
    api_token: str | None,
    callback_url: str,
) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "task-steward/1"

        def log_message(self, fmt: str, *args: object) -> None:
            return

        def _authorized(self) -> bool:
            if api_token is None:
                return True
            header = self.headers.get("Authorization", "")
            expected = f"Bearer {api_token}"
            return hmac.compare_digest(header, expected)

        def _json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _fail(self, exc: BaseException) -> None:
            if isinstance(exc, NoAssignment):
                code = 404
            elif isinstance(exc, (WorkerNotEligible, LeaseConflict, StaleLease)):
                code = 409
            elif isinstance(exc, InvalidLeaseToken):
                code = 403
            elif isinstance(exc, (ValueError, TypeError)):
                code = 400
            else:
                code = 500
            self._json(code, {"error": exc.__class__.__name__, "message": str(exc)})

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > 65536:
                raise ValueError("request body too large")
            body = self.rfile.read(length)
            payload = json.loads(body.decode("utf-8") or "{}")
            if not isinstance(payload, dict):
                raise ValueError("request JSON must be an object")
            return payload

        def do_GET(self) -> None:  # noqa: N802
            if not self._authorized():
                self._json(401, {"error": "unauthorized"})
                return
            parsed = urllib.parse.urlparse(self.path)
            query = urllib.parse.parse_qs(parsed.query)
            try:
                if parsed.path == "/v1/status":
                    result = actor.call("status")
                elif parsed.path == "/v1/assignment":
                    worker = query.get("worker", [""])[0]
                    result = actor.call("assignment", worker=worker).public_dict()
                else:
                    self._json(404, {"error": "not_found"})
                    return
                self._json(200, result)
            except BaseException as exc:
                self._fail(exc)

        def do_POST(self) -> None:  # noqa: N802
            if not self._authorized():
                self._json(401, {"error": "unauthorized"})
                return
            try:
                payload = self._read_json()
                if self.path == "/v1/receipt":
                    result = actor.call("receipt", payload=payload)
                elif self.path == "/v1/dispatch":
                    worker = str(payload.get("worker", ""))
                    result = actor.call("dispatch", worker=worker, callback_url=callback_url)
                else:
                    self._json(404, {"error": "not_found"})
                    return
                self._json(200, result)
            except BaseException as exc:
                self._fail(exc)

    return Handler


def serve(args: argparse.Namespace) -> None:
    api_token = os.environ.get("STEWARD_API_TOKEN")
    if not _is_loopback(args.host) and not api_token:
        raise SystemExit("non-loopback bind requires STEWARD_API_TOKEN")
    if not _is_loopback(args.host) and not args.public_url:
        raise SystemExit("non-loopback bind requires --public-url")

    base_callback = args.public_url.rstrip("/") if args.public_url else f"http://{args.host}:{args.port}"
    callback_url = base_callback + "/v1/receipt"
    actor = RuntimeActor(
        lambda: StewardRuntime(
            root=ROOT,
            workers_path=args.workers,
            db_path=args.db,
            ttl_seconds=args.ttl,
        )
    )
    server = ThreadingHTTPServer(
        (args.host, args.port),
        make_handler(actor, api_token=api_token, callback_url=callback_url),
    )
    try:
        server.serve_forever()
    finally:
        server.server_close()
        actor.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=Path, default=DEFAULT_WORKERS)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--ttl", type=int, default=3600)
    sub = parser.add_subparsers(dest="command", required=True)

    serve_parser = sub.add_parser("serve")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=9777)
    serve_parser.add_argument("--public-url")

    assignment_parser = sub.add_parser("assignment")
    assignment_parser.add_argument("--worker", required=True)

    dispatch_parser = sub.add_parser("dispatch")
    dispatch_parser.add_argument("--worker", required=True)
    dispatch_parser.add_argument("--callback-url")

    receipt_parser = sub.add_parser("receipt")
    receipt_parser.add_argument("--worker", required=True)
    receipt_parser.add_argument("--project", required=True)
    receipt_parser.add_argument("--task-ref", required=True)
    receipt_parser.add_argument("--generation", required=True, type=int)
    receipt_parser.add_argument("--lease-token", required=True)
    receipt_parser.add_argument("--kind", required=True, choices=sorted(RECEIPT_KINDS))
    receipt_parser.add_argument("--detail")

    sub.add_parser("status")
    args = parser.parse_args()

    if args.command == "serve":
        serve(args)
        return

    runtime = StewardRuntime(
        root=ROOT,
        workers_path=args.workers,
        db_path=args.db,
        ttl_seconds=args.ttl,
    )
    try:
        if args.command == "assignment":
            result = runtime.assignment(args.worker).public_dict()
        elif args.command == "dispatch":
            result = runtime.dispatch(args.worker, args.callback_url)
        elif args.command == "receipt":
            result = runtime.receipt(
                {
                    "worker": args.worker,
                    "project": args.project,
                    "task_ref": args.task_ref,
                    "generation": args.generation,
                    "lease_token": args.lease_token,
                    "kind": args.kind,
                    "detail": args.detail,
                }
            )
        else:
            result = runtime.status()
        print(json.dumps(result, sort_keys=True))
    finally:
        runtime.close()


if __name__ == "__main__":
    main()
