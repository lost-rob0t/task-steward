---
name: task-steward-worker
description: steward, rage, lease, worker, heartbeat, fencing
compatibility: Agent Skills-compatible coding agent with HTTP access to a Task Steward runtime and repository issue/PR tools
---

# Task Steward Worker

Execute one externally assigned RAGE transaction without becoming a scheduler.

## Input

An assignment contains:

- `worker`
- `project`
- `task_ref`
- `generation`
- `lease_token`
- `source`
- `receipt_url`

## Workflow

1. Treat the assignment as authoritative only while its lease is current.
2. Load the repository's `rage` skill and repository instructions.
3. Resolve `task_ref` to the canonical issue/PR in the assigned project.
4. Recover an existing safe transaction for that exact task before creating a replacement.
5. Never substitute another issue, PR, project, or backlog item on your own.
6. Send `heartbeat` or `status` receipts during long work.
7. Send `complete`, `blocked`, or `yield` only at a real transaction boundary.
8. Preserve `worker`, `project`, `task_ref`, `generation`, and `lease_token` exactly in every receipt.
9. If a receipt returns `revoked`, `StaleLease`, or a generation mismatch, stop state-changing work immediately.

## Receipt

POST JSON to the supplied `receipt_url`:

```json
{
  "worker": "WORKER",
  "project": "PROJECT",
  "task_ref": "TASK_REF",
  "generation": 1,
  "lease_token": "LEASE_TOKEN",
  "kind": "heartbeat",
  "detail": "short evidence-only status"
}
```

If `STEWARD_API_TOKEN` is configured, use `Authorization: Bearer $STEWARD_API_TOKEN`.
Never copy either API or lease tokens into commits, issues, PR text, durable logs, or reports.

## Rules

- Prolog owns global scheduling and worker eligibility.
- The worker owns only execution of the leased transaction.
- GitHub issue/PR state remains canonical implementation evidence.
- Exact-head CI and repository merge policy still apply.
- A lease is not permission to bypass repository authorization or validation.
- Missing steward connectivity is a blocker, not permission to freelance.
