#!/usr/bin/env python3
"""Compile authored deployment evidence into deterministic Prolog facts."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "state" / "deployment.yml"
DEFAULT_OUTPUT = ROOT / "kb" / "generated" / "deployment.pl"
ALLOWED_STATUSES = {"satisfied", "pending", "blocked"}
ALLOWED_STATES = {"building", "deployed"}


def atom(value: str) -> str:
    text = value.strip().lower().replace("-", "_")
    if not text or not text[0].isalpha() or any(not (c.isalnum() or c == "_") for c in text):
        raise ValueError(f"invalid steward atom: {value!r}")
    return text


def quoted(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def load_deployment(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    if not isinstance(doc, dict) or doc.get("version") != 1:
        raise ValueError(f"{path}: expected version: 1")
    return doc


def compile_deployment(doc: dict[str, Any]) -> str:
    state = doc.get("state")
    if state not in ALLOWED_STATES:
        raise ValueError(f"deployment state must be one of {sorted(ALLOWED_STATES)}")

    rows = doc.get("requirements")
    if not isinstance(rows, list) or not rows:
        raise ValueError("requirements must be a non-empty list")

    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("deployment requirement must be a mapping")
        ident = row.get("id")
        status = row.get("status")
        evidence = row.get("evidence", [])
        if not isinstance(ident, str) or not ident:
            raise ValueError("deployment requirement id is required")
        if ident in seen:
            raise ValueError(f"duplicate deployment requirement: {ident}")
        if status not in ALLOWED_STATUSES:
            raise ValueError(f"deployment requirement {ident}: invalid status {status!r}")
        if not isinstance(evidence, list) or any(not isinstance(item, str) or not item for item in evidence):
            raise ValueError(f"deployment requirement {ident}: evidence must be non-empty strings")
        if status == "satisfied" and not evidence:
            raise ValueError(f"deployment requirement {ident}: satisfied status requires evidence")
        seen.add(ident)
        normalized.append(row)

    lines = [
        "% GENERATED FILE. DO NOT EDIT.",
        "% Source: state/deployment.yml",
        ":- module(kb_generated_deployment, [deployment_declared_state/1, deployment_requirement/2, deployment_requirement_evidence/2]).",
        "",
        f"deployment_declared_state({atom(state)}).",
        "",
    ]
    for row in sorted(normalized, key=lambda item: item["id"]):
        ident = atom(row["id"])
        lines.append(f"deployment_requirement({ident}, {atom(row['status'])}).")
        for evidence in sorted(row.get("evidence", [])):
            lines.append(f"deployment_requirement_evidence({ident}, {quoted(evidence)}).")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = compile_deployment(load_deployment(DEFAULT_INPUT))
    if args.check:
        if not DEFAULT_OUTPUT.exists() or DEFAULT_OUTPUT.read_text(encoding="utf-8") != text:
            raise SystemExit("generated deployment KB is stale")
        return 0
    DEFAULT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
