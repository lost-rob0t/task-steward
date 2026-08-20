#!/usr/bin/env python3
"""Fail closed when Task Steward workflows exceed repository-local authority."""
from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

FORBIDDEN_ACTION_FRAGMENTS = (
    "gh repo clone",
    "git clone",
    "git push",
    "gh pr merge",
    "gh issue",
    "curl -x post",
    "curl --request post",
    "curl -x put",
    "curl --request put",
    "curl -x patch",
    "curl --request patch",
    "api.github.com/repos/",
)


def load_workflow(path: Path) -> dict:
    # PyYAML's YAML 1.1 loader treats `on` as boolean. BaseLoader preserves keys.
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.load(fh, Loader=yaml.BaseLoader)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: workflow must be a mapping")
    return data


def validate_permissions(path: Path, workflow: dict) -> None:
    permissions = workflow.get("permissions")
    if permissions != {"contents": "read"}:
        raise ValueError(f"{path}: top-level permissions must be exactly contents: read")

    for job_name, job in (workflow.get("jobs") or {}).items():
        if isinstance(job, dict) and "permissions" in job:
            raise ValueError(f"{path}: job {job_name} must not override permissions")


def validate_triggers(path: Path, workflow: dict) -> None:
    triggers = workflow.get("on") or {}
    if not isinstance(triggers, dict):
        raise ValueError(f"{path}: triggers must be a mapping")
    allowed = {"push", "pull_request", "workflow_dispatch"}
    unknown = set(triggers) - allowed
    if unknown:
        raise ValueError(f"{path}: unsupported trigger(s): {sorted(unknown)}")

    push = triggers.get("push") or {}
    if push and push.get("branches") != ["main"]:
        raise ValueError(f"{path}: push wake must be bounded to main")


def validate_steps(path: Path, workflow: dict) -> None:
    for job_name, job in (workflow.get("jobs") or {}).items():
        if not isinstance(job, dict):
            continue
        for step in job.get("steps") or []:
            if not isinstance(step, dict):
                continue
            action = (step.get("uses") or "").lower()
            if action and not re.fullmatch(r"actions/checkout@v\d+", action):
                raise ValueError(f"{path}: job {job_name} uses non-allow-listed action {action}")
            script = (step.get("run") or "").lower()
            for fragment in FORBIDDEN_ACTION_FRAGMENTS:
                if fragment in script:
                    raise ValueError(f"{path}: job {job_name} contains forbidden write primitive {fragment!r}")


def validate(path: Path) -> None:
    workflow = load_workflow(path)
    validate_permissions(path, workflow)
    validate_triggers(path, workflow)
    validate_steps(path, workflow)


def main() -> int:
    paths = sorted(WORKFLOWS.glob("*.yml")) + sorted(WORKFLOWS.glob("*.yaml"))
    if not paths:
        raise SystemExit("no workflows found")
    for path in paths:
        validate(path)
        print(f"workflow scope validated: {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
