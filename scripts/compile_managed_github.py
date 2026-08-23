#!/usr/bin/env python3
"""Compile bounded managed-repository GitHub evidence into deterministic Prolog facts."""
from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "state" / "managed_github.yml"
DEFAULT_PROJECTS = ROOT / "state" / "projects.yml"
DEFAULT_OUTPUT = ROOT / "kb" / "generated" / "managed_github.pl"
MAX_PROJECTS = 64
MAX_WORK_PER_PROJECT = 256
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SNAPSHOTS = {"fresh", "partial", "stale", "unavailable"}
KINDS = {"issue", "pr", "followup"}
STATES = {"open", "closed"}
SEVERITIES = {"critical", "high", "normal", "low"}
READINESS = {"ready", "blocked", "pending"}
CI_STATES = {"success", "failure", "pending", "unknown", "not_applicable"}
REVIEW_STATES = {"clean", "blocked", "pending", "unknown", "not_applicable"}


def atom(value: str) -> str:
    text = value.strip().lower().replace("-", "_")
    if not text or not text[0].isalpha() or any(not (c.isalnum() or c == "_") for c in text):
        raise ValueError(f"invalid steward atom: {value!r}")
    return text


def quoted(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def timestamp(value: Any, field: str) -> str:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"{field} must be an ISO-8601 timestamp") from exc
    else:
        raise ValueError(f"{field} must be an ISO-8601 timestamp")
    if dt.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return dt.isoformat()


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    if not isinstance(doc, dict) or doc.get("version") != 1:
        raise ValueError(f"{path}: expected version: 1")
    return doc


def project_map(projects_doc: dict[str, Any]) -> dict[str, str]:
    rows = projects_doc.get("projects")
    if not isinstance(rows, list):
        raise ValueError("projects.yml projects must be a list")
    result: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("project entry must be a mapping")
        ident, repo = row.get("id"), row.get("repo")
        if not isinstance(ident, str) or not isinstance(repo, str):
            raise ValueError("project requires id and repo")
        result[ident] = repo
    return result


def validate_work(project: str, repo: str, row: Any, seen_refs: set[str], seen_sources: set[str]) -> dict[str, Any]:
    if not isinstance(row, dict):
        raise ValueError(f"{project}: work entry must be a mapping")
    required = ("ref", "kind", "number", "state", "severity", "readiness", "ci", "review", "updated_at", "source")
    missing = [key for key in required if key not in row]
    if missing:
        raise ValueError(f"{project}: work entry missing {', '.join(missing)}")
    ref, kind, number = row["ref"], row["kind"], row["number"]
    if not isinstance(ref, str) or not re.fullmatch(r"(?:issue|pr|followup)-[1-9][0-9]*", ref):
        raise ValueError(f"{project}: invalid work ref {ref!r}")
    if ref in seen_refs:
        raise ValueError(f"{project}: duplicate work ref {ref}")
    seen_refs.add(ref)
    if kind not in KINDS or not isinstance(number, int) or isinstance(number, bool) or number <= 0:
        raise ValueError(f"{project}: invalid kind/number for {ref}")
    if ref != f"{kind}-{number}":
        raise ValueError(f"{project}: ref {ref} does not match kind/number")
    for field, allowed in (("state", STATES), ("severity", SEVERITIES), ("readiness", READINESS), ("ci", CI_STATES), ("review", REVIEW_STATES)):
        if row[field] not in allowed:
            raise ValueError(f"{project}: invalid {field} {row[field]!r} for {ref}")
    source = row["source"]
    expected_source = f"github-{kind}:{repo}#{number}"
    if not isinstance(source, str) or source != expected_source:
        raise ValueError(f"{project}: source must be {expected_source}")
    if source in seen_sources:
        raise ValueError(f"duplicate managed GitHub source: {source}")
    seen_sources.add(source)
    head_sha = row.get("head_sha")
    if kind == "pr":
        if not isinstance(head_sha, str) or not SHA_RE.fullmatch(head_sha):
            raise ValueError(f"{project}: PR {ref} requires a 40-character lowercase head_sha")
    elif head_sha is not None:
        raise ValueError(f"{project}: non-PR {ref} may not declare head_sha")
    return {
        **row,
        "updated_at": timestamp(row["updated_at"], f"{project}.{ref}.updated_at"),
    }


def normalize(doc: dict[str, Any], projects_doc: dict[str, Any]) -> dict[str, Any]:
    known = project_map(projects_doc)
    rows = doc.get("projects")
    if not isinstance(rows, list) or len(rows) > MAX_PROJECTS:
        raise ValueError(f"projects must be a list of at most {MAX_PROJECTS} entries")
    observed_by = doc.get("observed_by")
    if not isinstance(observed_by, str) or not observed_by.strip():
        raise ValueError("observed_by is required")
    observed_at = timestamp(doc.get("observed_at"), "observed_at")
    seen_projects: set[str] = set()
    seen_sources: set[str] = set()
    normalized_projects = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("managed project entry must be a mapping")
        project, repo, snapshot = row.get("project"), row.get("repo"), row.get("snapshot")
        if not isinstance(project, str) or project not in known:
            raise ValueError(f"unknown managed project: {project!r}")
        if project == "task-stward-rage":
            raise ValueError("Task Steward self issues belong in state/tasks.yml, not managed GitHub evidence")
        if project in seen_projects:
            raise ValueError(f"duplicate managed project: {project}")
        seen_projects.add(project)
        if not isinstance(repo, str) or not REPO_RE.fullmatch(repo) or repo != known[project]:
            raise ValueError(f"{project}: repo must exactly match projects.yml")
        if snapshot not in SNAPSHOTS:
            raise ValueError(f"{project}: invalid snapshot state {snapshot!r}")
        project_observed_at = timestamp(row.get("observed_at"), f"{project}.observed_at")
        work_rows = row.get("work", [])
        if not isinstance(work_rows, list) or len(work_rows) > MAX_WORK_PER_PROJECT:
            raise ValueError(f"{project}: work must contain at most {MAX_WORK_PER_PROJECT} entries")
        seen_refs: set[str] = set()
        work = [validate_work(project, repo, item, seen_refs, seen_sources) for item in work_rows]
        normalized_projects.append({
            "project": project,
            "repo": repo,
            "snapshot": snapshot,
            "observed_at": project_observed_at,
            "work": sorted(work, key=lambda item: (item["kind"], item["number"])),
        })
    return {
        "observed_by": observed_by,
        "observed_at": observed_at,
        "projects": sorted(normalized_projects, key=lambda item: item["project"]),
    }


def compile_managed(doc: dict[str, Any], projects_doc: dict[str, Any]) -> str:
    data = normalize(doc, projects_doc)
    lines = [
        "% GENERATED FILE. DO NOT EDIT.",
        "% Source: state/managed_github.yml",
        ":- module(kb_generated_managed_github, [managed_observed_by/1, managed_observed_at/1, github_snapshot/4, github_work/2, github_work_kind/3, github_work_state/3, github_work_severity/3, github_work_readiness/3, github_work_ci/3, github_work_review/3, github_work_head_sha/3, github_work_updated_at/3, github_work_source/3]).",
        "",
        f"managed_observed_by({atom(data['observed_by'])}).",
        f"managed_observed_at({quoted(data['observed_at'])}).",
        "",
    ]
    for project in data["projects"]:
        ident = atom(project["project"])
        lines.append(f"github_snapshot({ident}, {quoted(project['repo'])}, {atom(project['snapshot'])}, {quoted(project['observed_at'])}).")
        for item in project["work"]:
            ref = atom(item["ref"])
            lines.extend([
                f"github_work({ident}, {ref}).",
                f"github_work_kind({ident}, {ref}, {atom(item['kind'])}).",
                f"github_work_state({ident}, {ref}, {atom(item['state'])}).",
                f"github_work_severity({ident}, {ref}, {atom(item['severity'])}).",
                f"github_work_readiness({ident}, {ref}, {atom(item['readiness'])}).",
                f"github_work_ci({ident}, {ref}, {atom(item['ci'])}).",
                f"github_work_review({ident}, {ref}, {atom(item['review'])}).",
            ])
            if item.get("head_sha"):
                lines.append(f"github_work_head_sha({ident}, {ref}, {quoted(item['head_sha'])}).")
            lines.extend([
                f"github_work_updated_at({ident}, {ref}, {quoted(item['updated_at'])}).",
                f"github_work_source({ident}, {ref}, {quoted(item['source'])}).",
                "",
            ])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = compile_managed(load_yaml(DEFAULT_INPUT), load_yaml(DEFAULT_PROJECTS))
    if args.check:
        if not DEFAULT_OUTPUT.exists() or DEFAULT_OUTPUT.read_text(encoding="utf-8") != text:
            raise SystemExit("generated managed GitHub KB is stale")
        return 0
    DEFAULT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
