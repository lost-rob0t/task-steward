#!/usr/bin/env python3
"""Compile authored automation reconciliation YAML into deterministic Prolog facts."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "state" / "automations.yml"
DEFAULT_OUTPUT = ROOT / "kb" / "generated" / "automations.pl"


def atom(value: str) -> str:
    text = value.strip().lower().replace("-", "_")
    if not text or not text[0].isalpha() or any(not (c.isalnum() or c == "_") for c in text):
        raise ValueError(f"invalid steward atom: {value!r}")
    return text


def quoted(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def load_automations(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    if not isinstance(doc, dict) or doc.get("version") != 1:
        raise ValueError(f"{path}: expected version: 1")
    return doc


def compile_automations(doc: dict[str, Any]) -> str:
    active = doc.get("active") or []
    paused = doc.get("paused") or []
    if not isinstance(active, list) or not isinstance(paused, list):
        raise ValueError("active and paused must be lists")

    entries: list[tuple[str, str, dict[str, Any]]] = []
    seen: set[str] = set()
    for state, rows in (("active", active), ("paused", paused)):
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError(f"{state} automation must be a mapping")
            ident = row.get("id")
            title = row.get("title")
            if not isinstance(ident, str) or not ident or not isinstance(title, str) or not title:
                raise ValueError(f"{state} automation requires id and title")
            if ident in seen:
                raise ValueError(f"duplicate automation id: {ident}")
            seen.add(ident)
            entries.append((ident, state, row))

    reconciliation = doc.get("reconciliation") or {}
    if not isinstance(reconciliation, dict):
        raise ValueError("reconciliation must be a mapping")
    declared = reconciliation.get("active_task_count")
    if declared != len(active):
        raise ValueError(f"active_task_count {declared!r} does not match active entries {len(active)}")

    lines = [
        "% GENERATED FILE. DO NOT EDIT.",
        "% Source: state/automations.yml",
        ":- module(kb_generated_automations, [automation/1, automation_state/2, automation_title/2, automation_project/2, observed_by/1, observed_at/1, reconciliation_value/2, reconciliation_member/2]).",
        "",
    ]
    for ident, state, row in sorted(entries):
        lines.append(f"automation({quoted(ident)}).")
        lines.append(f"automation_state({quoted(ident)}, {state}).")
        lines.append(f"automation_title({quoted(ident)}, {quoted(row['title'])}).")
        project = row.get("project")
        if isinstance(project, str) and project:
            lines.append(f"automation_project({quoted(ident)}, {atom(project)}).")
        lines.append("")

    observed_by = doc.get("observed_by")
    observed_at = doc.get("observed_at")
    if not isinstance(observed_by, str) or not isinstance(observed_at, str):
        raise ValueError("observed_by and observed_at are required strings")
    lines.append(f"observed_by({atom(observed_by)}).")
    normalized_at = observed_at.replace("Z", "+00:00")
    lines.append(f"observed_at({quoted(normalized_at)}).")

    for key in sorted(reconciliation):
        value = reconciliation[key]
        path = f"[{atom(str(key))}]"
        if isinstance(value, list):
            for item in value:
                if not isinstance(item, str):
                    raise ValueError(f"reconciliation.{key} list values must be strings")
                lines.append(f"reconciliation_member({path}, {atom(item)}).")
        elif isinstance(value, bool):
            lines.append(f"reconciliation_value({path}, {'true' if value else 'false'}).")
        elif isinstance(value, int):
            lines.append(f"reconciliation_value({path}, {value}).")
        elif isinstance(value, str):
            lines.append(f"reconciliation_value({path}, {atom(value)}).")
        else:
            raise ValueError(f"unsupported reconciliation value for {key}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = compile_automations(load_automations(DEFAULT_INPUT))
    if args.check:
        if not DEFAULT_OUTPUT.exists() or DEFAULT_OUTPUT.read_text(encoding="utf-8") != text:
            raise SystemExit("generated automation KB is stale")
        return 0
    DEFAULT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
