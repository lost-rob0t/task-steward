#!/usr/bin/env python3
"""Compile authored steward policy YAML into deterministic Prolog facts."""
from __future__ import annotations

import argparse
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICIES = ROOT / "state" / "policies.yml"
DEFAULT_OUTPUT = ROOT / "kb" / "generated" / "policies.pl"
ATOM_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def prolog_atom(value: str) -> str:
    atom = value.strip().lower().replace("-", "_")
    if not ATOM_RE.fullmatch(atom):
        raise ValueError(f"invalid policy identifier: {value!r}")
    return atom


def quote_atom(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def scalar_term(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, (date, datetime)):
        return quote_atom(value.isoformat())
    if value is None:
        return "none"
    if isinstance(value, str):
        try:
            return prolog_atom(value)
        except ValueError:
            return quote_atom(value)
    raise ValueError(f"unsupported policy scalar: {value!r}")


def path_term(path: tuple[str, ...]) -> str:
    return "[" + ", ".join(prolog_atom(part) for part in path) + "]"


def load_policies(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    if not isinstance(doc, dict):
        raise ValueError(f"{path}: expected mapping")
    version = doc.get("version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise ValueError(f"{path}: version must be a positive integer")
    return doc


def _flatten_policy(
    value: Any,
    path: tuple[str, ...],
    facts: list[str],
) -> None:
    if isinstance(value, dict):
        for raw_key in sorted(value, key=str):
            if not isinstance(raw_key, str) or not raw_key:
                raise ValueError(f"invalid policy key at {path!r}: {raw_key!r}")
            _flatten_policy(value[raw_key], path + (raw_key,), facts)
        return

    if isinstance(value, list):
        for item in value:
            if isinstance(item, (dict, list)):
                raise ValueError(f"nested policy list structures are unsupported at {path!r}")
            facts.append(f"policy_member({path_term(path)}, {scalar_term(item)}).")
        return

    facts.append(f"policy_value({path_term(path)}, {scalar_term(value)}).")


def compile_policies(doc: dict[str, Any]) -> str:
    version = doc.get("version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise ValueError("policies: version must be a positive integer")

    facts = [f"policy_version({version})."]
    for raw_key in sorted(key for key in doc if key != "version"):
        if not isinstance(raw_key, str) or not raw_key:
            raise ValueError(f"invalid top-level policy key: {raw_key!r}")
        _flatten_policy(doc[raw_key], (raw_key,), facts)

    return """% GENERATED FILE. DO NOT EDIT.\n% Source: state/policies.yml\n:- module(kb_generated_policies, [\n    policy_version/1,\n    policy_value/2,\n    policy_member/2\n]).\n\n""" + "\n".join(facts) + "\n"


def write_or_check(path: Path, content: str, *, check: bool) -> None:
    if check:
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != content:
            label = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
            raise SystemExit(f"generated file is stale: {label}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if generated output is stale")
    parser.add_argument("--policies", type=Path, default=DEFAULT_POLICIES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    policies = load_policies(args.policies)
    compiled = compile_policies(policies)
    write_or_check(args.output, compiled, check=args.check)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
