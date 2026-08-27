#!/usr/bin/env python3
"""Compile portable worker runtime metadata into deterministic Prolog facts."""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKERS = ROOT / "state" / "workers.yml"
DEFAULT_KB = ROOT / "kb" / "generated" / "workers.pl"
ATOM_RE = re.compile(r"^[a-z][a-z0-9_]*$")
ENV_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
A0_TOKEN_RE = re.compile(r"/a2a/t-[^/\s]+")
SECRET_KEY_RE = re.compile(r"(?:^|_)(token|password|secret|api_key|authorization|cookie)(?:$|_)")
BACKENDS = frozenset({"agent-zero-a2a", "opencode-run", "operator-http"})


def prolog_atom(value: str) -> str:
    atom = value.strip().lower().replace("-", "_")
    if not ATOM_RE.fullmatch(atom):
        raise ValueError(f"invalid steward identifier: {value!r}")
    return atom


def quote_atom(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def load_workers(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    if not isinstance(doc, dict) or doc.get("version") != 1:
        raise ValueError(f"{path}: expected version: 1")
    workers = doc.get("workers")
    if not isinstance(workers, list) or not workers:
        raise ValueError(f"{path}: workers must be a non-empty list")
    return workers


def _validate_config(worker_id: str, backend: str, config: Any) -> dict[str, str]:
    if not isinstance(config, dict):
        raise ValueError(f"{worker_id}: config must be a mapping")
    normalized: dict[str, str] = {}
    for raw_key, value in config.items():
        if not isinstance(raw_key, str) or not isinstance(value, str) or not value:
            raise ValueError(f"{worker_id}: config keys and values must be non-empty strings")
        key = raw_key.strip()
        if SECRET_KEY_RE.search(key.lower()) and not key.lower().endswith("_env"):
            raise ValueError(f"{worker_id}: secret-bearing key {key!r} is forbidden; use *_env indirection")
        if A0_TOKEN_RE.search(value):
            raise ValueError(f"{worker_id}: embedded Agent Zero token is forbidden")
        if key.endswith("_env") and not ENV_RE.fullmatch(value):
            raise ValueError(f"{worker_id}: {key} must name an environment variable")
        normalized[key] = value

    required: tuple[str, ...]
    if backend == "agent-zero-a2a":
        required = ("base_url_env", "token_env", "project")
    elif backend == "opencode-run":
        required = ("binary_env", "workdir_env")
    else:
        required = ()
    missing = [key for key in required if key not in normalized]
    if missing:
        raise ValueError(f"{worker_id}: backend {backend} requires {', '.join(missing)}")
    return normalized


def compile_workers(workers: list[dict[str, Any]]) -> str:
    facts: list[str] = []
    seen: set[str] = set()
    for index, worker in enumerate(workers):
        if not isinstance(worker, dict):
            raise ValueError(f"worker #{index + 1}: expected mapping")
        raw_id = worker.get("id")
        raw_project = worker.get("project")
        backend = worker.get("backend")
        enabled = worker.get("enabled")
        if not all(isinstance(v, str) and v for v in (raw_id, raw_project, backend)):
            raise ValueError(f"worker #{index + 1}: id/project/backend are required strings")
        if enabled not in (True, False):
            raise ValueError(f"{raw_id}: enabled must be a boolean")
        if backend not in BACKENDS:
            raise ValueError(f"{raw_id}: unsupported backend {backend!r}")

        wid = prolog_atom(raw_id)
        project = prolog_atom(raw_project)
        backend_atom = prolog_atom(backend)
        if wid in seen:
            raise ValueError(f"duplicate worker id: {raw_id}")
        seen.add(wid)

        config = _validate_config(raw_id, backend, worker.get("config") or {})
        capabilities = worker.get("capabilities") or []
        if not isinstance(capabilities, list) or not all(
            isinstance(item, str) and item for item in capabilities
        ):
            raise ValueError(f"{raw_id}: capabilities must be a list of identifiers")

        facts.append(f"worker({wid}).")
        facts.append(f"worker_project({wid}, {project}).")
        facts.append(f"worker_backend({wid}, {backend_atom}).")
        facts.append(f"worker_{'enabled' if enabled else 'disabled'}({wid}).")
        for capability in sorted({prolog_atom(item) for item in capabilities}):
            facts.append(f"worker_capability({wid}, {capability}).")
        for key, value in sorted(config.items()):
            facts.append(f"worker_config({wid}, {prolog_atom(key)}, {quote_atom(value)}).")
        facts.append("")

    return """% GENERATED FILE. DO NOT EDIT.\n% Source: state/workers.yml\n:- module(kb_generated_workers, [\n    worker/1,\n    worker_project/2,\n    worker_backend/2,\n    worker_enabled/1,\n    worker_disabled/1,\n    worker_capability/2,\n    worker_config/3\n]).\n\n""" + "\n".join(facts).rstrip() + "\n"


def write_or_check(path: Path, content: str, *, check: bool) -> None:
    if check:
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != content:
            raise SystemExit(f"stale generated worker facts: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_WORKERS)
    parser.add_argument("--output", type=Path, default=DEFAULT_KB)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    workers = load_workers(args.input)
    write_or_check(args.output, compile_workers(workers), check=args.check)


if __name__ == "__main__":
    main()
