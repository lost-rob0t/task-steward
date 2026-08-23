#!/usr/bin/env python3
"""Reconcile a canonical repository issue snapshot into durable task state."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from reconcile_issue_task import (
    DEFAULT_STATE,
    EXPECTED_REPOSITORY,
    dump_yaml,
    load_yaml,
    reconcile_event,
)


def flatten_snapshot(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        raise ValueError("issue snapshot must be a list")

    rows: list[Any] = []
    for item in payload:
        if isinstance(item, list):
            rows.extend(item)
        else:
            rows.append(item)

    issues: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("issue snapshot rows must be mappings")
        if "pull_request" in row:
            continue
        number = row.get("number")
        state = row.get("state")
        updated_at = row.get("updated_at")
        if not isinstance(number, int) or isinstance(number, bool) or number <= 0:
            raise ValueError("snapshot issue number must be a positive integer")
        if state not in {"open", "closed"}:
            raise ValueError(f"unsupported snapshot issue state: {state!r}")
        if not isinstance(updated_at, str) or not updated_at:
            raise ValueError("snapshot issue updated_at is required")
        issues.append(row)

    issues.sort(key=lambda row: (row["updated_at"], row["number"]))
    return issues


def reconcile_snapshot(doc: dict[str, Any], payload: Any) -> dict[str, Any]:
    result = doc
    for issue in flatten_snapshot(payload):
        event = {
            "repository": {"full_name": EXPECTED_REPOSITORY},
            "issue": issue,
        }
        result = reconcile_event(result, event)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot-json", type=Path, required=True)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    args = parser.parse_args()

    with args.snapshot_json.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    current = load_yaml(args.state)
    reconciled = reconcile_snapshot(current, payload)
    text = dump_yaml(reconciled)
    if args.state.read_text(encoding="utf-8") != text:
        args.state.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
