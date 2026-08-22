#!/usr/bin/env python3
"""Reconcile one repository-local GitHub Issue event into durable task state."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATE = ROOT / "state" / "tasks.yml"
EXPECTED_REPOSITORY = "lost-rob0t/task-stward-rage"
PROJECT = "task-stward-rage"
DEFAULT_PRIORITY = 10


def reconcile_event(doc: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(doc, dict) or doc.get("version") != 1:
        raise ValueError("task state must use version 1")

    repository = event.get("repository")
    full_name = repository.get("full_name") if isinstance(repository, dict) else None
    if full_name != EXPECTED_REPOSITORY:
        raise ValueError(f"foreign repository event rejected: {full_name!r}")

    issue = event.get("issue")
    if not isinstance(issue, dict):
        raise ValueError("event requires issue payload")
    number = issue.get("number")
    state = issue.get("state")
    updated_at = issue.get("updated_at")
    if not isinstance(number, int) or isinstance(number, bool) or number <= 0:
        raise ValueError("issue number must be a positive integer")
    if state not in {"open", "closed"}:
        raise ValueError(f"unsupported issue state: {state!r}")
    if not isinstance(updated_at, str) or not updated_at:
        raise ValueError("issue updated_at is required")

    result = copy.deepcopy(doc)
    rows = result.get("tasks")
    if not isinstance(rows, list):
        raise ValueError("tasks must be a list")

    ident = f"task-stward-rage-issue-{number}"
    source = f"github-issue:{EXPECTED_REPOSITORY}#{number}"
    matches = [row for row in rows if isinstance(row, dict) and (row.get("id") == ident or row.get("source") == source)]
    if len(matches) > 1:
        raise ValueError(f"duplicate durable task for issue #{number}")

    if matches:
        row = matches[0]
        if row.get("id") != ident or row.get("source") != source:
            raise ValueError(f"durable task identity mismatch for issue #{number}")
        generation = row.get("generation", 0)
        if not isinstance(generation, int) or isinstance(generation, bool) or generation < 0:
            raise ValueError(f"invalid task generation for issue #{number}")
        if row.get("state") != state:
            row["state"] = state
            row["generation"] = generation + 1
    else:
        rows.append(
            {
                "id": ident,
                "project": PROJECT,
                "source": source,
                "state": state,
                "priority": DEFAULT_PRIORITY,
                "generation": 1,
            }
        )

    rows.sort(key=lambda row: row["id"])
    result["observed_by"] = "task-steward"
    result["observed_at"] = updated_at
    return result


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    if not isinstance(doc, dict):
        raise ValueError(f"{path}: expected mapping")
    return doc


def dump_yaml(doc: dict[str, Any]) -> str:
    return yaml.safe_dump(doc, sort_keys=False, default_flow_style=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-json", type=Path, required=True)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    args = parser.parse_args()

    with args.event_json.open("r", encoding="utf-8") as fh:
        event = json.load(fh)
    current = load_yaml(args.state)
    reconciled = reconcile_event(current, event)
    text = dump_yaml(reconciled)
    if args.state.read_text(encoding="utf-8") != text:
        args.state.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
