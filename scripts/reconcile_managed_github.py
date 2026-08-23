#!/usr/bin/env python3
"""Snapshot managed GitHub repositories as bounded read-only steward evidence."""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
PROJECTS_PATH = ROOT / "state" / "projects.yml"
OUTPUT_PATH = ROOT / "state" / "managed_github.yml"
API_ROOT = "https://api.github.com"
GRAPHQL_URL = "https://api.github.com/graphql"
MAX_WORK_PER_PROJECT = 256
PAGE_SIZE = 100
MAX_PAGES = 3
BLOCKING_LABELS = {"blocked", "waiting", "waiting-on-dependency", "dependencies"}
FOLLOWUP_LABELS = {"followup", "follow-up", "post-merge", "postmerge"}
CRITICAL_LABELS = {"critical", "p0", "sev0", "severity:critical"}
HIGH_LABELS = {"high", "p1", "sev1", "severity:high"}
LOW_LABELS = {"low", "p3", "sev3", "severity:low"}
FAIL_CONCLUSIONS = {"failure", "cancelled", "timed_out", "action_required", "startup_failure", "stale"}
SUCCESS_CONCLUSIONS = {"success", "neutral", "skipped"}

GRAPHQL_REVIEW_QUERY = """
query ManagedPullReview($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      reviewDecision
      reviewThreads(first: 100) {
        nodes { isResolved }
        pageInfo { hasNextPage }
      }
    }
  }
}
""".strip()


class GithubReadError(RuntimeError):
    pass


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def token() -> str | None:
    return os.environ.get("TASK_STEWARD_GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")


def request_json(url: str, *, auth: str | None, data: bytes | None = None) -> tuple[Any, dict[str, str]]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "task-steward-managed-github-reconciler",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if auth:
        headers["Authorization"] = f"Bearer {auth}"
    method = "POST" if data is not None else "GET"
    request = urllib.request.Request(url, headers=headers, data=data, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return payload, {key.lower(): value for key, value in response.headers.items()}
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise GithubReadError(f"read failed for {url}: {exc}") from exc


def rest_get(path: str, auth: str | None) -> Any:
    payload, _ = request_json(f"{API_ROOT}{path}", auth=auth)
    return payload


def paged_get(path: str, auth: str | None) -> tuple[list[dict[str, Any]], bool]:
    rows: list[dict[str, Any]] = []
    complete = True
    separator = "&" if "?" in path else "?"
    for page in range(1, MAX_PAGES + 1):
        payload = rest_get(f"{path}{separator}per_page={PAGE_SIZE}&page={page}", auth)
        if not isinstance(payload, list):
            raise GithubReadError(f"expected list response for {path}")
        rows.extend(item for item in payload if isinstance(item, dict))
        if len(payload) < PAGE_SIZE:
            break
    else:
        complete = False
    if len(rows) > MAX_WORK_PER_PROJECT:
        rows = rows[:MAX_WORK_PER_PROJECT]
        complete = False
    return rows, complete


def labels(row: dict[str, Any]) -> set[str]:
    result: set[str] = set()
    for label in row.get("labels") or []:
        if isinstance(label, dict) and isinstance(label.get("name"), str):
            result.add(label["name"].strip().lower())
        elif isinstance(label, str):
            result.add(label.strip().lower())
    return result


def severity_from_labels(names: set[str]) -> str:
    if names & CRITICAL_LABELS:
        return "critical"
    if names & HIGH_LABELS:
        return "high"
    if names & LOW_LABELS:
        return "low"
    return "normal"


def issue_readiness(names: set[str]) -> str:
    return "blocked" if names & BLOCKING_LABELS else "ready"


def classify_ci(check_runs: list[dict[str, Any]], combined_status: dict[str, Any] | None) -> str:
    if any(run.get("status") != "completed" for run in check_runs):
        return "pending"
    conclusions = {str(run.get("conclusion") or "").lower() for run in check_runs}
    if conclusions & FAIL_CONCLUSIONS:
        return "failure"
    status_state = str((combined_status or {}).get("state") or "").lower()
    statuses = (combined_status or {}).get("statuses") or []
    if status_state in {"pending", "expected"} or any(str(item.get("state") or "").lower() in {"pending", "expected"} for item in statuses if isinstance(item, dict)):
        return "pending"
    if status_state in {"failure", "error"} or any(str(item.get("state") or "").lower() in {"failure", "error"} for item in statuses if isinstance(item, dict)):
        return "failure"
    if not check_runs and not statuses:
        return "unknown"
    if conclusions - SUCCESS_CONCLUSIONS:
        return "unknown"
    if status_state and status_state not in {"success"}:
        return "unknown"
    return "success"


def pull_ci(repo: str, sha: str, auth: str | None) -> str:
    check_payload = rest_get(f"/repos/{repo}/commits/{sha}/check-runs?per_page=100", auth)
    status_payload = rest_get(f"/repos/{repo}/commits/{sha}/status", auth)
    check_runs = check_payload.get("check_runs") if isinstance(check_payload, dict) else None
    if not isinstance(check_runs, list) or not isinstance(status_payload, dict):
        raise GithubReadError(f"invalid exact-head status response for {repo}@{sha}")
    return classify_ci([item for item in check_runs if isinstance(item, dict)], status_payload)


def graphql_review(repo: str, number: int, auth: str | None) -> tuple[str, int]:
    if not auth:
        return "unknown", 0
    owner, name = repo.split("/", 1)
    body = json.dumps({
        "query": GRAPHQL_REVIEW_QUERY,
        "variables": {"owner": owner, "name": name, "number": number},
    }).encode("utf-8")
    payload, _ = request_json(GRAPHQL_URL, auth=auth, data=body)
    if not isinstance(payload, dict) or payload.get("errors"):
        raise GithubReadError(f"GraphQL review query failed for {repo}#{number}")
    pull = (((payload.get("data") or {}).get("repository") or {}).get("pullRequest"))
    if not isinstance(pull, dict):
        raise GithubReadError(f"missing pull request review data for {repo}#{number}")
    threads = pull.get("reviewThreads") or {}
    nodes = threads.get("nodes") or []
    unresolved = sum(1 for item in nodes if isinstance(item, dict) and item.get("isResolved") is False)
    if unresolved:
        return "blocked", unresolved
    if ((threads.get("pageInfo") or {}).get("hasNextPage")):
        return "unknown", 0
    decision = str(pull.get("reviewDecision") or "").upper()
    if decision == "CHANGES_REQUESTED":
        return "blocked", 0
    if decision == "APPROVED":
        return "clean", 0
    if decision == "REVIEW_REQUIRED":
        return "pending", 0
    return "unknown", 0


def issue_work(repo: str, row: dict[str, Any]) -> dict[str, Any]:
    number = int(row["number"])
    names = labels(row)
    kind = "followup" if names & FOLLOWUP_LABELS else "issue"
    return {
        "ref": f"{kind}-{number}",
        "kind": kind,
        "number": number,
        "state": "open",
        "severity": severity_from_labels(names),
        "readiness": issue_readiness(names),
        "ci": "not_applicable",
        "review": "not_applicable",
        "updated_at": row.get("updated_at") or now_iso(),
        "source": f"github-{kind}:{repo}#{number}",
    }


def pull_work(repo: str, row: dict[str, Any], auth: str | None) -> tuple[dict[str, Any], bool]:
    number = int(row["number"])
    sha = (((row.get("head") or {}).get("sha")))
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise GithubReadError(f"missing exact PR head for {repo}#{number}")
    partial = False
    try:
        ci = pull_ci(repo, sha, auth)
    except GithubReadError:
        ci = "unknown"
        partial = True
    try:
        review, _unresolved = graphql_review(repo, number, auth)
    except GithubReadError:
        review = "unknown"
        partial = True
    return ({
        "ref": f"pr-{number}",
        "kind": "pr",
        "number": number,
        "state": "open",
        "severity": severity_from_labels(labels(row)),
        "readiness": "ready",
        "ci": ci,
        "review": review,
        "head_sha": sha,
        "updated_at": row.get("updated_at") or now_iso(),
        "source": f"github-pr:{repo}#{number}",
    }, partial)


def snapshot_project(project: str, repo: str, auth: str | None, observed_at: str) -> dict[str, Any]:
    try:
        issue_rows, issues_complete = paged_get(f"/repos/{repo}/issues?state=open", auth)
        pull_rows, pulls_complete = paged_get(f"/repos/{repo}/pulls?state=open", auth)
    except GithubReadError as exc:
        print(f"managed GitHub unavailable for {repo}: {exc}", file=sys.stderr)
        return {"project": project, "repo": repo, "snapshot": "unavailable", "observed_at": observed_at, "work": []}

    partial = not (issues_complete and pulls_complete)
    work: list[dict[str, Any]] = []
    for row in issue_rows:
        if "pull_request" not in row:
            work.append(issue_work(repo, row))
    for row in pull_rows:
        try:
            item, item_partial = pull_work(repo, row, auth)
            work.append(item)
            partial = partial or item_partial
        except (GithubReadError, KeyError, TypeError, ValueError) as exc:
            partial = True
            print(f"managed GitHub partial PR evidence for {repo}: {exc}", file=sys.stderr)
    if len(work) > MAX_WORK_PER_PROJECT:
        work = work[:MAX_WORK_PER_PROJECT]
        partial = True
    work.sort(key=lambda item: (item["kind"], item["number"]))
    return {
        "project": project,
        "repo": repo,
        "snapshot": "partial" if partial else "fresh",
        "observed_at": observed_at,
        "work": work,
    }


def load_projects() -> list[tuple[str, str]]:
    with PROJECTS_PATH.open("r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    rows = doc.get("projects") if isinstance(doc, dict) else None
    if not isinstance(rows, list):
        raise ValueError("state/projects.yml must contain projects")
    projects: list[tuple[str, str]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("project entry must be a mapping")
        ident, repo = row.get("id"), row.get("repo")
        if not isinstance(ident, str) or not isinstance(repo, str):
            raise ValueError("project entry requires id/repo")
        if ident != "task-stward-rage":
            projects.append((ident, repo))
    return sorted(projects)


def main() -> int:
    observed_at = now_iso()
    auth = token()
    projects = [snapshot_project(project, repo, auth, observed_at) for project, repo in load_projects()]
    doc = {
        "version": 1,
        "observed_by": "task-steward-github",
        "observed_at": observed_at,
        "projects": projects,
    }
    OUTPUT_PATH.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    print(f"reconciled {len(projects)} managed GitHub projects at {observed_at}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
