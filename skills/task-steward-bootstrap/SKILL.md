---
name: task-steward-bootstrap
description: steward, bootstrap, workers, a0, opencode, adapters
compatibility: Agent Skills-compatible coding agent with git, Python 3, SWI-Prolog, and access to the Task Steward checkout
---

# Task Steward Bootstrap

Bootstrap a runtime-independent Task Steward worker without changing scheduling authority.

## Goal

Turn a checked-out Task Steward control plane into a worker service usable by Agent Zero, OpenCode, or a generic HTTP-capable agent.

## Workflow

1. Read `AGENTS.md`, `state/projects.yml`, and `state/workers.yml`.
2. Confirm `swipl`, Python 3, and PyYAML are available.
3. Add or edit worker metadata in `state/workers.yml`; store only environment-variable names for credentials.
4. Run `python3 scripts/compile_workers.py` and then `python3 scripts/compile_workers.py --check`.
5. Query `swipl -q -s steward.pl -g "steward_validate,halt"` before starting a runtime.
6. Configure backend environment variables outside git.
7. Start `python3 scripts/steward_runtime.py serve` on loopback by default.
8. For Agent Zero, enable A2A and point the worker at the A0 base URL plus token env vars.
9. For OpenCode, configure the binary/worktree env vars; dispatch uses non-interactive `opencode run`.
10. Generic agents use `/v1/assignment` and `/v1/receipt` directly and follow `task-steward-worker`.

## Adapter views

`skills/` is canonical in this repository. Runtime-specific project views are links/adapters only:

- `.a0proj/skills/` — Agent Zero project override
- `.agents/skills/` — OpenCode and generic Agent Skills clients
- `.a0/skills/` — local compatibility view; do not treat it as Agent Zero's canonical discovery path

Never maintain independent copies of the same skill body.

## Security

- Never commit A0 tokens, API keys, passwords, lease tokens, or receipt auth tokens.
- Non-loopback steward binding requires `STEWARD_API_TOKEN` and an explicit public callback URL.
- Do not expose the runtime directly to the Internet without a trusted TLS/reverse-proxy boundary.
- A backend failure yields its lease; it does not authorize choosing replacement work.
