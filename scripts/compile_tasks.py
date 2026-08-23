#!/usr/bin/env python3
"""Compile durable task scheduling metadata into deterministic Prolog facts."""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "state" / "tasks.yml"
DEFAULT_OUTPUT = ROOT / "kb" / "generated" / "tasks.pl"


def atom(value: str) -> str:
    text = value.strip().lower().replace("-", "_")
    if not text or not text[0].isalpha() or any(not (c.isalnum() or c == "_") for c in text):
        raise ValueError(f"invalid steward atom: {value!r}")
    return text


def quoted(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def load_tasks(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    if not isinstance(doc, dict) or doc.get("version") != 1:
        raise ValueError(f"{path}: expected version: 1")
    return doc


def compile_tasks(doc: dict[str, Any]) -> str:
    rows = doc.get("tasks") or []
    if not isinstance(rows, list):
        raise ValueError("tasks must be a list")

    seen_ids: set[str] = set()
    seen_sources: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("task must be a mapping")
        ident = row.get("id")
        project = row.get("project")
        source = row.get("source")
        state = row.get("state")
        priority = row.get("priority", 0)
        generation = row.get("generation", 0)
        if not all(isinstance(value, str) and value for value in (ident, project, source, state)):
            raise ValueError("task requires id, project, source, and state")
        if ident in seen_ids:
            raise ValueError(f"duplicate task id: {ident}")
        if source in seen_sources:
            raise ValueError(f"duplicate task source: {source}")
        if not isinstance(priority, int) or isinstance(priority, bool):
            raise ValueError(f"task {ident}: priority must be an integer")
        if not isinstance(generation, int) or isinstance(generation, bool) or generation < 0:
            raise ValueError(f"task {ident}: generation must be a non-negative integer")
        dependencies = row.get("dependencies") or []
        if not isinstance(dependencies, list) or any(not isinstance(dep, str) or not dep for dep in dependencies):
            raise ValueError(f"task {ident}: dependencies must be task ids")
        seen_ids.add(ident)
        seen_sources.add(source)
        normalized.append(row)

    known = {row["id"] for row in normalized}
    for row in normalized:
        unknown = sorted(set(row.get("dependencies") or []) - known)
        if unknown:
            raise ValueError(f"task {row['id']}: unknown dependencies: {', '.join(unknown)}")

    lines = [
        "% GENERATED FILE. DO NOT EDIT.",
        "% Source: state/tasks.yml",
        ":- module(kb_generated_tasks, [task/1, task_project/2, task_source/2, task_state/2, task_priority/2, task_dependency/2, task_generation/2, observed_by/1, observed_at/1]).",
        "",
    ]
    has_dependencies = False
    for row in sorted(normalized, key=lambda item: item["id"]):
        ident = atom(row["id"])
        lines.append(f"task({ident}).")
        lines.append(f"task_project({ident}, {atom(row['project'])}).")
        lines.append(f"task_source({ident}, {quoted(row['source'])}).")
        lines.append(f"task_state({ident}, {atom(row['state'])}).")
        lines.append(f"task_priority({ident}, {row.get('priority', 0)}).")
        lines.append(f"task_generation({ident}, {row.get('generation', 0)}).")
        for dependency in sorted(row.get("dependencies") or []):
            has_dependencies = True
            lines.append(f"task_dependency({ident}, {atom(dependency)}).")
        lines.append("")

    if not has_dependencies:
        lines.append("task_dependency(_, _) :- fail.")
        lines.append("")

    observed_by = doc.get("observed_by")
    observed_at = doc.get("observed_at")
    if not isinstance(observed_by, str) or not observed_by:
        raise ValueError("observed_by is required")
    if isinstance(observed_at, datetime):
        normalized_at = observed_at.isoformat()
    elif isinstance(observed_at, str) and observed_at:
        normalized_at = observed_at.replace("Z", "+00:00")
    else:
        raise ValueError("observed_at is required")
    lines.append(f"observed_by({atom(observed_by)}).")
    lines.append(f"observed_at({quoted(normalized_at)}).")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = compile_tasks(load_tasks(DEFAULT_INPUT))
    if args.check:
        if not DEFAULT_OUTPUT.exists() or DEFAULT_OUTPUT.read_text(encoding="utf-8") != text:
            raise SystemExit("generated task KB is stale")
        return 0
    DEFAULT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
