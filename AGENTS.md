# Task Steward RAGE Instructions

This repository is the private durable state and expert-system control plane for the Task Steward.

## Hard isolation boundary

- Only the Task Steward may use or mutate this repository.
- Managed project repositories must never clone, import, vendor, dispatch into, write to, or depend on this repository.
- Never copy implementation code from managed repositories into this repository.
- Never use this repository as a shared library for managed projects.
- External repositories are references/evidence only. GitHub Issues in their owning repositories remain the canonical implementation tasks.
- This repository may contain mirrored facts about external repositories only when the Task Steward observed those facts and records provenance.
- A workflow in this repository must not mutate a managed project repository.

## RAGE

RAGE means **Recursive Analysis with Gated Execution**.

Every loop starts from observed state, derives admissible actions through explicit rules, records evidence, and recurses from the result. A plan, model output, existing branch, empty commit, or green build is not itself authorization.

## Repository model

- `state/` contains steward-authored policy plus bounded observed/derived orchestration state.
- `kb/` contains Prolog knowledge-base facts and derived/mirrored state.
- `experts/` contains serial Prolog Mixture-of-Experts rule modules.
- `steward.pl` is the unified Prolog interface. Consumers must not bypass it to invent alternate scheduling authority.
- `.github/workflows/` may validate, reconcile evidence, and wake the steward, but must remain scoped to this repository.
- `skills/` is the canonical repository-local worker/bootstrap skill source. Client-specific project views are adapters only.

There is intentionally no managed-project source tree here.

## Client skill adapters

When acting as an external worker or bootstrapping one, read the canonical `skills/task-steward-worker/SKILL.md` or `skills/task-steward-bootstrap/SKILL.md` contract before execution.

- `.a0proj/skills/` is the Agent Zero project-scope adapter.
- `.agents/skills/` is the generic/OpenCode project-scope adapter.
- `.a0/skills/` is a local compatibility adapter only; Agent Zero's documented project discovery path is `.a0proj/skills/`.
- Adapter entries must point back to the canonical `skills/` packages. Never hand-maintain divergent copies.

## Managed GitHub scheduling authority

- `state/managed_github.yml` is the bounded, provenance-bearing observation of managed repository backlog/PR/CI/review state.
- `kb/generated/managed_github.pl` is its deterministic Prolog representation.
- `state/managed_decisions.json` is generated from `steward.pl`; it is not hand-authored policy. It records Prolog's current `keep`/`pause`/`yield` worker decisions and `next_external` candidate.
- The Task Steward must consume the current `state/managed_decisions.json` from canonical `main` when deciding which managed workers stay active and what external work is next. Do not substitute an LLM-selected worker/task when a current Prolog decision exists.
- A newer explicit user instruction may change policy, but reconcile that instruction into durable policy/project state and regenerate/re-evaluate Prolog before treating the changed schedule as canonical.
- Missing, stale, partial, inaccessible, or truncated GitHub evidence must fail closed. It may retain a worker or permit already-observed positive work, but it must never be treated as proof that a worker should be yielded.
- Explicit user hard stops and resume-required states are absolute and cannot be overridden by backlog pressure.

## YAML and inline Prolog

YAML is the ergonomic authoring format. It may contain inline Prolog extension blocks for project-specific facts, policy, completion gates, scoring, or expert behavior.

Inline Prolog is logic-only. It must be parsed/validated before loading. Reject directives or predicates that grant filesystem, process, shell, network, foreign-library, arbitrary consult/load, or equivalent side-effect authority. Custom rules may reason only over the steward's allow-listed logical interface and may define new pure predicates.

## Serial Prolog MoE

The experts are Prolog rule modules, not LLM personas. Run them serially over the same KB and derived facts. The Prolog system owns scheduling, worker retention, priority scoring, failure classification, regression detection, job/test skipping, handoffs, and completion decisions.

An LLM may perform bounded work selected by the steward, but LLM output is evidence/input, never direct scheduling authority.

## Issues are actual tasks

Use GitHub Issues for actual implementation work. Do not create a second prose copy of an issue in this repository. The KB may store references, state, score, dependencies, leases, attempts, and outcomes for an issue.

For self-RAGE work on this repository, create an issue here before implementation.

## Wake commits

The Task Steward may create an empty commit to trigger a new GitHub Actions evaluation. A wake commit means only that state may have changed and should be re-evaluated. It must not encode an unreviewed decision that bypasses Prolog.

State-maintenance commits generated by workflows must not recursively wake themselves without an explicit steward wake marker.

## Evidence and history

Never fabricate task state, CI status, completion, failure, approval, regression, or handoff evidence. Persist enough provenance to explain why a decision was made. Retries and handoffs must be idempotent where practical. A stale or failed run must never silently become success.

## Scope of writes

Before every write, verify the target repository is exactly `lost-rob0t/task-stward-rage`. If not, abort the write.
