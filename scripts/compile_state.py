#!/usr/bin/env python3
"""Compile Task Steward authored YAML into deterministic Prolog modules.

This compiler is intentionally narrow: it only reads this repository's state/
files and only writes generated files inside this repository.  It does not
contact GitHub or any managed project repository.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROJECTS = ROOT / "state" / "projects.yml"
DEFAULT_KB = ROOT / "kb" / "generated" / "projects.pl"
DEFAULT_RULES = ROOT / "experts" / "generated" / "project_rules.pl"

ATOM_RE = re.compile(r"^[a-z][a-z0-9_]*$")
DIRECTIVE_RE = re.compile(r"(?m)^\s*:-")
QUERY_RE = re.compile(r"(?m)^\s*\?-")

# Inline rules are logic-only.  This is deliberately conservative and will be
# tightened into an AST/predicate allow-list in a later Issue #1 slice.
FORBIDDEN_CALLS = {
    "shell",
    "process_create",
    "process_wait",
    "open",
    "close",
    "delete_file",
    "rename_file",
    "make_directory",
    "delete_directory",
    "consult",
    "ensure_loaded",
    "load_files",
    "use_module",
    "use_foreign_library",
    "load_foreign_library",
    "http_open",
    "http_get",
    "http_post",
    "tcp_connect",
    "tcp_socket",
    "udp_socket",
    "set_prolog_flag",
    "halt",
}


def prolog_atom(value: str) -> str:
    atom = value.strip().lower().replace("-", "_")
    if not ATOM_RE.fullmatch(atom):
        raise ValueError(f"invalid steward identifier: {value!r}")
    return atom


def quote_atom(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def validate_inline_prolog(text: str, *, source: str) -> str:
    """Reject side-effect authority while preserving ordinary pure rules."""
    if not isinstance(text, str):
        raise ValueError(f"{source}: inline Prolog must be a string")
    normalized = text.strip()
    if not normalized:
        return ""
    if DIRECTIVE_RE.search(normalized):
        raise ValueError(f"{source}: Prolog directives are forbidden")
    if QUERY_RE.search(normalized):
        raise ValueError(f"{source}: Prolog queries are forbidden")

    for name in sorted(FORBIDDEN_CALLS):
        if re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}\s*\(", normalized):
            raise ValueError(f"{source}: forbidden predicate {name}/...")

    # Module qualification can escape the steward predicate surface.
    if re.search(r"\b[a-z][a-z0-9_]*\s*:\s*[a-z][a-z0-9_]*\s*\(", normalized):
        raise ValueError(f"{source}: module-qualified calls are forbidden")

    return normalized + "\n"


def load_projects(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    if not isinstance(doc, dict) or doc.get("version") != 1:
        raise ValueError(f"{path}: expected version: 1")
    projects = doc.get("projects")
    if not isinstance(projects, list) or not projects:
        raise ValueError(f"{path}: projects must be a non-empty list")
    return projects


def compile_projects(projects: list[dict[str, Any]]) -> tuple[str, str]:
    facts: list[str] = []
    custom_rules: list[str] = []
    seen: set[str] = set()

    for index, project in enumerate(projects):
        if not isinstance(project, dict):
            raise ValueError(f"project #{index + 1}: expected mapping")
        raw_id = project.get("id")
        repo = project.get("repo")
        status = project.get("status")
        mode = project.get("mode")
        if not all(isinstance(v, str) and v for v in (raw_id, repo, status, mode)):
            raise ValueError(f"project #{index + 1}: id/repo/status/mode are required strings")

        pid = prolog_atom(raw_id)
        if pid in seen:
            raise ValueError(f"duplicate project id: {raw_id}")
        seen.add(pid)

        facts.append(f"project({pid}).")
        facts.append(f"project_repo({pid}, {quote_atom(repo)}).")
        facts.append(f"project_status({pid}, {prolog_atom(status)}).")
        facts.append(f"project_mode({pid}, {prolog_atom(mode)}).")

        priority = project.get("priority") or {}
        if not isinstance(priority, dict):
            raise ValueError(f"{raw_id}: priority must be a mapping")
        base = priority.get("base", 0)
        if not isinstance(base, int):
            raise ValueError(f"{raw_id}: priority.base must be an integer")
        facts.append(f"base_priority({pid}, {base}).")
        if priority.get("protected") is True:
            facts.append(f"protected_project({pid}).")

        completion = project.get("completion") or {}
        if not isinstance(completion, dict):
            raise ValueError(f"{raw_id}: completion must be a mapping")
        gate = completion.get("gate")
        if gate is not None:
            if not isinstance(gate, str) or not gate:
                raise ValueError(f"{raw_id}: completion.gate must be a string")
            facts.append(f"completion_policy({pid}, {prolog_atom(gate)}).")

        rules = project.get("rules") or {}
        if not isinstance(rules, dict):
            raise ValueError(f"{raw_id}: rules must be a mapping")
        inline = rules.get("prolog")
        if inline is not None:
            checked = validate_inline_prolog(inline, source=f"{raw_id}.rules.prolog")
            if checked:
                custom_rules.append(f"% project: {raw_id}\n{checked.rstrip()}")

        facts.append("")

    kb = """% GENERATED FILE. DO NOT EDIT.\n% Source: state/projects.yml\n:- module(kb_generated_projects, [\n    project/1,\n    project_repo/2,\n    project_status/2,\n    project_mode/2,\n    base_priority/2,\n    protected_project/1,\n    completion_policy/2\n]).\n\n""" + "\n".join(facts).rstrip() + "\n"

    rules = """% GENERATED FILE. DO NOT EDIT.\n% Source: state/projects.yml inline Prolog blocks\n:- module(generated_project_rules, []).\n\n"""
    if custom_rules:
        rules += "\n\n".join(custom_rules).rstrip() + "\n"

    return kb, rules


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
    parser.add_argument("--projects", type=Path, default=DEFAULT_PROJECTS)
    parser.add_argument("--kb-output", type=Path, default=DEFAULT_KB)
    parser.add_argument("--rules-output", type=Path, default=DEFAULT_RULES)
    args = parser.parse_args()

    projects = load_projects(args.projects)
    kb, rules = compile_projects(projects)
    write_or_check(args.kb_output, kb, check=args.check)
    write_or_check(args.rules_output, rules, check=args.check)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
