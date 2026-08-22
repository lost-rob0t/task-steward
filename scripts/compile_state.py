#!/usr/bin/env python3
"""Compile Task Steward authored YAML into deterministic Prolog modules.

This compiler only reads this repository's state and writes generated files
inside this repository. Inline Prolog is parsed by SWI-Prolog and restricted to
an explicit logical predicate allow-list before it can become generated code.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Iterable

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROJECTS = ROOT / "state" / "projects.yml"
DEFAULT_HANDOFFS = ROOT / "state" / "handoffs.yml"
DEFAULT_KB = ROOT / "kb" / "generated" / "projects.pl"
DEFAULT_RULES = ROOT / "experts" / "generated" / "project_rules.pl"
DEFAULT_EXPERT_REGISTRY = ROOT / "experts" / "generated" / "registry.pl"
DEFAULT_HANDOFF_KB = ROOT / "kb" / "generated" / "handoffs.pl"
DEFAULT_HANDOFF_RULES = ROOT / "experts" / "generated" / "handoff_rules.pl"
INLINE_VALIDATOR = ROOT / "scripts" / "validate_inline_prolog.pl"

ATOM_RE = re.compile(r"^[a-z][a-z0-9_]*$")
PREDICATE_INDICATOR_RE = re.compile(r"^[a-z][a-z0-9_]*/(?:0|[1-9][0-9]*)$")
DIRECTIVE_RE = re.compile(r"(?m)^\s*:-")
QUERY_RE = re.compile(r"(?m)^\s*\?-")

STAGE_BASE = {
    "eligibility": 10,
    "dependencies": 20,
    "failure": 30,
    "regression": 40,
    "priority": 50,
    "skip_policy": 60,
    "scheduling": 70,
    "handoff": 80,
    "completion": 90,
}
BUILTIN_EXPERTS = frozenset(STAGE_BASE)


def prolog_atom(value: str) -> str:
    atom = value.strip().lower().replace("-", "_")
    if not ATOM_RE.fullmatch(atom):
        raise ValueError(f"invalid steward identifier: {value!r}")
    return atom


def quote_atom(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def normalize_predicate_indicators(values: Iterable[str], *, source: str) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str) or not PREDICATE_INDICATOR_RE.fullmatch(value):
            raise ValueError(f"{source}: invalid predicate indicator {value!r}")
        normalized.append(value)
    return tuple(sorted(set(normalized)))


def validate_inline_prolog(
    text: str,
    *,
    source: str,
    allowed_predicates: Iterable[str] = (),
) -> str:
    """Parse rules and reject every body call outside the logical allow-list."""
    if not isinstance(text, str):
        raise ValueError(f"{source}: inline Prolog must be a string")
    normalized = text.strip()
    if not normalized:
        return ""
    if DIRECTIVE_RE.search(normalized):
        raise ValueError(f"{source}: Prolog directives are forbidden")
    if QUERY_RE.search(normalized):
        raise ValueError(f"{source}: Prolog queries are forbidden")

    allowed = normalize_predicate_indicators(allowed_predicates, source=source)
    with tempfile.NamedTemporaryFile("w", suffix=".pl", encoding="utf-8", delete=False) as fh:
        fh.write(normalized)
        fh.write("\n")
        temp_path = Path(fh.name)

    try:
        try:
            proc = subprocess.run(
                ["swipl", "-q", "-s", str(INLINE_VALIDATOR), "--", str(temp_path), *allowed],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise ValueError(f"{source}: SWI-Prolog is required for inline rule validation") from exc
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout).strip().splitlines()
            reason = detail[-1] if detail else "validator rejected inline Prolog"
            raise ValueError(f"{source}: {reason}")
    finally:
        temp_path.unlink(missing_ok=True)

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


def load_handoffs(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    if not isinstance(doc, dict) or doc.get("version") != 1:
        raise ValueError(f"{path}: expected version: 1")
    handoffs = doc.get("handoffs")
    if not isinstance(handoffs, list) or not handoffs:
        raise ValueError(f"{path}: handoffs must be a non-empty list")
    return handoffs


def _collect_custom_expert_names(projects: list[dict[str, Any]]) -> set[str]:
    names: set[str] = set()
    for index, project in enumerate(projects):
        if not isinstance(project, dict):
            raise ValueError(f"project #{index + 1}: expected mapping")
        raw_id = project.get("id", f"project-{index + 1}")
        experts = project.get("experts") or []
        if not isinstance(experts, list):
            raise ValueError(f"{raw_id}: experts must be a list")
        for expert in experts:
            if not isinstance(expert, dict) or not isinstance(expert.get("name"), str):
                raise ValueError(f"{raw_id}: every custom expert needs a name")
            name = prolog_atom(expert["name"])
            if name in BUILTIN_EXPERTS or name in names:
                raise ValueError(f"{raw_id}: duplicate/reserved expert name {expert['name']!r}")
            names.add(name)
    return names


def compile_projects(projects: list[dict[str, Any]]) -> tuple[str, str, str]:
    facts: list[str] = []
    custom_rules: list[str] = []
    custom_registry: list[tuple[int, str, str, tuple[str, ...]]] = []
    seen: set[str] = set()
    custom_names = _collect_custom_expert_names(projects)

    for index, project in enumerate(projects):
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
        if not isinstance(base, int) or isinstance(base, bool):
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
        allowed = rules.get("allowed_predicates") or []
        if not isinstance(allowed, list):
            raise ValueError(f"{raw_id}: rules.allowed_predicates must be a list")
        inline = rules.get("prolog")
        if inline is not None:
            checked = validate_inline_prolog(
                inline,
                source=f"{raw_id}.rules.prolog",
                allowed_predicates=allowed,
            )
            if checked:
                custom_rules.append(f"% project: {raw_id}\n{checked.rstrip()}")

        experts = project.get("experts") or []
        for expert in experts:
            name = prolog_atom(expert["name"])
            raw_stage = expert.get("stage")
            if not isinstance(raw_stage, str):
                raise ValueError(f"{raw_id}.{name}: stage is required")
            stage = prolog_atom(raw_stage)
            if stage not in STAGE_BASE:
                raise ValueError(f"{raw_id}.{name}: unknown stage {raw_stage!r}")
            offset = expert.get("order", 1)
            if not isinstance(offset, int) or isinstance(offset, bool) or not 1 <= offset <= 9:
                raise ValueError(f"{raw_id}.{name}: order must be an integer from 1 through 9")
            deps_raw = expert.get("depends_on") or []
            if not isinstance(deps_raw, list) or not all(isinstance(dep, str) for dep in deps_raw):
                raise ValueError(f"{raw_id}.{name}: depends_on must be a list of expert names")
            deps = tuple(prolog_atom(dep) for dep in deps_raw)
            known = BUILTIN_EXPERTS | custom_names
            unknown = sorted(dep for dep in deps if dep not in known)
            if unknown:
                raise ValueError(f"{raw_id}.{name}: unknown expert dependencies {unknown}")
            effective_order = STAGE_BASE[stage] + offset
            custom_registry.append((effective_order, name, stage, deps))

        facts.append("")

    custom_registry.sort(key=lambda item: (item[0], item[1]))
    seen_orders: dict[int, str] = {}
    for effective_order, name, _, _ in custom_registry:
        other = seen_orders.get(effective_order)
        if other is not None:
            raise ValueError(
                f"custom experts {other!r} and {name!r} have the same effective order {effective_order}"
            )
        seen_orders[effective_order] = name

    kb = """% GENERATED FILE. DO NOT EDIT.\n% Source: state/projects.yml\n:- module(kb_generated_projects, [\n    project/1,\n    project_repo/2,\n    project_status/2,\n    project_mode/2,\n    base_priority/2,\n    protected_project/1,\n    completion_policy/2\n]).\n\n""" + "\n".join(facts).rstrip() + "\n"

    rules_text = """% GENERATED FILE. DO NOT EDIT.\n% Source: state/projects.yml inline Prolog blocks\n:- module(generated_project_rules, []).\n\n"""
    if custom_rules:
        rules_text += "\n\n".join(custom_rules).rstrip() + "\n"

    registry_lines = [
        "% GENERATED FILE. DO NOT EDIT.",
        "% Source: state/projects.yml custom experts",
        ":- module(generated_expert_registry, [",
        "    custom_expert/1,",
        "    custom_expert_stage/2,",
        "    custom_expert_order/2,",
        "    custom_expert_dependency/2",
        "]).",
        "",
    ]
    for effective_order, name, stage, deps in custom_registry:
        registry_lines.extend(
            [
                f"custom_expert({name}).",
                f"custom_expert_stage({name}, {stage}).",
                f"custom_expert_order({name}, {effective_order}).",
            ]
        )
        registry_lines.extend(f"custom_expert_dependency({name}, {dep})." for dep in deps)
        registry_lines.append("")
    registry = "\n".join(registry_lines).rstrip() + "\n"

    return kb, rules_text, registry


def compile_handoffs(handoffs: list[dict[str, Any]]) -> tuple[str, str]:
    facts: list[str] = []
    custom_rules: list[str] = []
    seen: set[str] = set()

    for index, handoff in enumerate(handoffs):
        if not isinstance(handoff, dict):
            raise ValueError(f"handoff #{index + 1}: expected mapping")
        raw_id = handoff.get("id")
        source = handoff.get("from")
        target = handoff.get("to")
        status = handoff.get("status")
        gate = handoff.get("completion_gate")
        if not all(isinstance(v, str) and v for v in (raw_id, source, target, status, gate)):
            raise ValueError(
                f"handoff #{index + 1}: id/from/to/status/completion_gate are required strings"
            )

        hid = prolog_atom(raw_id)
        if hid in seen:
            raise ValueError(f"duplicate handoff id: {raw_id}")
        seen.add(hid)
        source_atom = prolog_atom(source)
        target_atom = prolog_atom(target)

        facts.append(f"handoff({hid}, {source_atom}, {target_atom}).")
        facts.append(f"handoff_status({hid}, {prolog_atom(status)}).")
        facts.append(f"handoff_gate({hid}, {prolog_atom(gate)}).")

        require = handoff.get("require") or {}
        if not isinstance(require, dict):
            raise ValueError(f"{raw_id}: require must be a mapping")
        required = require.get("all") or []
        if not isinstance(required, list) or not all(isinstance(item, str) and item for item in required):
            raise ValueError(f"{raw_id}: require.all must be a list of identifiers")
        for requirement in required:
            facts.append(f"handoff_requirement({hid}, {prolog_atom(requirement)}).")

        rules = handoff.get("rules") or {}
        if not isinstance(rules, dict):
            raise ValueError(f"{raw_id}: rules must be a mapping")
        allowed = rules.get("allowed_predicates") or []
        if not isinstance(allowed, list):
            raise ValueError(f"{raw_id}: rules.allowed_predicates must be a list")
        inline = rules.get("prolog")
        if inline is not None:
            checked = validate_inline_prolog(
                inline,
                source=f"{raw_id}.rules.prolog",
                allowed_predicates=allowed,
            )
            if checked:
                custom_rules.append(f"% handoff: {raw_id}\n{checked.rstrip()}")

        facts.append("")

    kb = """% GENERATED FILE. DO NOT EDIT.\n% Source: state/handoffs.yml\n:- module(kb_generated_handoffs, [\n    handoff/3,\n    handoff_status/2,\n    handoff_gate/2,\n    handoff_requirement/2\n]).\n\n""" + "\n".join(facts).rstrip() + "\n"

    rules_text = """% GENERATED FILE. DO NOT EDIT.\n% Source: state/handoffs.yml inline Prolog blocks\n:- module(generated_handoff_rules, [handoff_ready/1]).\n\n:- use_module('../../kb/generated/projects.pl').\n:- use_module('../../kb/evidence.pl').\n:- multifile handoff_ready/1.\n\n"""
    if custom_rules:
        rules_text += "\n\n".join(custom_rules).rstrip() + "\n"

    return kb, rules_text


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
    parser.add_argument("--handoffs", type=Path, default=DEFAULT_HANDOFFS)
    parser.add_argument("--kb-output", type=Path, default=DEFAULT_KB)
    parser.add_argument("--rules-output", type=Path, default=DEFAULT_RULES)
    parser.add_argument("--expert-registry-output", type=Path, default=DEFAULT_EXPERT_REGISTRY)
    parser.add_argument("--handoff-kb-output", type=Path, default=DEFAULT_HANDOFF_KB)
    parser.add_argument("--handoff-rules-output", type=Path, default=DEFAULT_HANDOFF_RULES)
    args = parser.parse_args()

    projects = load_projects(args.projects)
    kb, rules, registry = compile_projects(projects)
    handoffs = load_handoffs(args.handoffs)
    handoff_kb, handoff_rules = compile_handoffs(handoffs)
    write_or_check(args.kb_output, kb, check=args.check)
    write_or_check(args.rules_output, rules, check=args.check)
    write_or_check(args.expert_registry_output, registry, check=args.check)
    write_or_check(args.handoff_kb_output, handoff_kb, check=args.check)
    write_or_check(args.handoff_rules_output, handoff_rules, check=args.check)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
