#!/usr/bin/env python3
"""Fail closed when Task Steward workflows exceed repository-local authority."""
from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
TASK_RECONCILE_WORKFLOW = "task-reconcile.yml"
TASK_RECONCILE_CRON = "17 * * * *"
TASK_RECONCILE_GH_API = 'gh api --paginate --slurp "repos/${github_repository}/issues?state=all&per_page=100" > "$runner_temp/issues.json"'
TASK_RECONCILE_GIT_ADD = "git add -f -- state/tasks.yml kb/generated/tasks.pl"
MANAGED_RECONCILE_WORKFLOW = "managed-reconcile.yml"
MANAGED_RECONCILE_CRON = "37 * * * *"
MANAGED_RECONCILE_PATHS = [
    ".github/workflows/managed-reconcile.yml",
    "state/projects.yml",
    "scripts/reconcile_managed_github.py",
    "scripts/compile_managed_github.py",
    "scripts/export_managed_decisions.pl",
]
MANAGED_RECONCILE_GIT_ADD = "git add -f -- state/managed_github.yml state/managed_decisions.json kb/generated/managed_github.pl"
STATE_WRITER_CONCURRENCY = {"group": "task-steward-state-writers", "cancel-in-progress": "false"}

FORBIDDEN_ACTION_FRAGMENTS = (
    "gh repo clone",
    "git clone",
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


def is_task_reconcile(path: Path) -> bool:
    return path.name == TASK_RECONCILE_WORKFLOW


def is_managed_reconcile(path: Path) -> bool:
    return path.name == MANAGED_RECONCILE_WORKFLOW


def is_repo_writer(path: Path) -> bool:
    return is_task_reconcile(path) or is_managed_reconcile(path)


def load_workflow(path: Path) -> dict:
    # PyYAML's YAML 1.1 loader treats `on` as boolean. BaseLoader preserves keys.
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.load(fh, Loader=yaml.BaseLoader)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: workflow must be a mapping")
    return data


def validate_permissions(path: Path, workflow: dict) -> None:
    if is_task_reconcile(path):
        expected = {"contents": "write", "issues": "read"}
    elif is_managed_reconcile(path):
        expected = {"contents": "write"}
    else:
        expected = {"contents": "read"}
    permissions = workflow.get("permissions")
    if permissions != expected:
        raise ValueError(f"{path}: permissions must be exactly {expected}")

    for job_name, job in (workflow.get("jobs") or {}).items():
        if isinstance(job, dict) and "permissions" in job:
            raise ValueError(f"{path}: job {job_name} must not override permissions")


def validate_concurrency(path: Path, workflow: dict) -> None:
    if is_repo_writer(path):
        if workflow.get("concurrency") != STATE_WRITER_CONCURRENCY:
            raise ValueError(f"{path}: state writers must use the shared serialized concurrency group")


def validate_triggers(path: Path, workflow: dict) -> None:
    triggers = workflow.get("on") or {}
    if not isinstance(triggers, dict):
        raise ValueError(f"{path}: triggers must be a mapping")

    if is_task_reconcile(path):
        expected = {"issues", "pull_request", "schedule", "workflow_dispatch"}
        if set(triggers) != expected:
            raise ValueError(f"{path}: task reconcile triggers must be exactly {sorted(expected)}")
        issues = triggers.get("issues") or {}
        if issues.get("types") != ["opened", "closed", "reopened"]:
            raise ValueError(f"{path}: task reconcile issue types must be opened, closed, reopened")
        pull_request = triggers.get("pull_request") or {}
        if pull_request.get("types") != ["closed"]:
            raise ValueError(f"{path}: task reconcile pull request types must be exactly closed")
        schedule = triggers.get("schedule") or []
        if schedule != [{"cron": TASK_RECONCILE_CRON}]:
            raise ValueError(f"{path}: task reconcile schedule must be exactly {TASK_RECONCILE_CRON!r}")
        return

    if is_managed_reconcile(path):
        expected = {"push", "schedule", "workflow_dispatch"}
        if set(triggers) != expected:
            raise ValueError(f"{path}: managed reconcile triggers must be exactly {sorted(expected)}")
        push = triggers.get("push") or {}
        if push.get("branches") != ["main"] or push.get("paths") != MANAGED_RECONCILE_PATHS:
            raise ValueError(f"{path}: managed reconcile push trigger must be exactly bounded to main and approved paths")
        schedule = triggers.get("schedule") or []
        if schedule != [{"cron": MANAGED_RECONCILE_CRON}]:
            raise ValueError(f"{path}: managed reconcile schedule must be exactly {MANAGED_RECONCILE_CRON!r}")
        return

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
            script = step.get("run") or ""
            lowered = script.lower()
            push_lines = [line.strip().lower() for line in script.splitlines() if "git push" in line.lower()]
            if push_lines:
                if not is_repo_writer(path) or push_lines != ["git push origin head:main"]:
                    raise ValueError(f"{path}: job {job_name} contains forbidden write primitive 'git push'")
            api_lines = [line.strip().lower() for line in script.splitlines() if "gh api" in line.lower()]
            if api_lines:
                if not is_task_reconcile(path) or api_lines != [TASK_RECONCILE_GH_API]:
                    raise ValueError(f"{path}: job {job_name} contains non-allow-listed GitHub API access")
            git_add_lines = [line.strip().lower() for line in script.splitlines() if "git add" in line.lower()]
            if git_add_lines:
                if is_task_reconcile(path):
                    if git_add_lines != [TASK_RECONCILE_GIT_ADD]:
                        raise ValueError(f"{path}: job {job_name} generated task staging must use the exact forced allow-listed command")
                elif is_managed_reconcile(path):
                    if git_add_lines != [MANAGED_RECONCILE_GIT_ADD]:
                        raise ValueError(f"{path}: job {job_name} managed GitHub staging must use the exact forced allow-listed command")
                else:
                    raise ValueError(f"{path}: job {job_name} contains forbidden staging primitive 'git add'")
            commit_lines = [line.strip().lower() for line in script.splitlines() if line.strip().lower().startswith("git commit")]
            if commit_lines and not is_repo_writer(path):
                raise ValueError(f"{path}: job {job_name} contains forbidden write primitive 'git commit'")
            for fragment in FORBIDDEN_ACTION_FRAGMENTS:
                if fragment in lowered:
                    raise ValueError(f"{path}: job {job_name} contains forbidden write primitive {fragment!r}")


def validate(path: Path) -> None:
    workflow = load_workflow(path)
    validate_permissions(path, workflow)
    validate_concurrency(path, workflow)
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
