# Hackmode Program — Mara Worker Setup (2026-09-04)

Canonical facts for all hackmode workers. Keep current; update on changes.

## Ownership & Endpoints
- Operator: nsaspy. Worker identity: mara (git.starintel.actor, uid 5, write access to nsaspy/hackmode).
- Code repo: https://git.starintel.actor/nsaspy/hackmode (Gitea; 27 open issues at setup time). Clone target: /a0/usr/workdir/hackmode-repo
- Steward control plane: /a0/usr/projects/task-steward (git.starintel.actor/mara/task-steward, PRIVATE).
  - Hard isolation: managed repos (hackmode) must never clone/import/dispatch into the steward repo. Only the Task Steward mutates steward state.
- Hackmode ops project (skills, promptinclude, scan conventions): /a0/usr/projects/hackmode

## Workers (Agent Zero scheduler, /a0/usr/scheduler/tasks.json, tz America/New_York)
1. hackmode-reviewer — scheduled 08:30 & 20:30 daily. Read-only review: recent commits + code in nsaspy/hackmode for bugs and features advancing "most interactive Common Lisp exploit framework + recon pipelining". Files labeled, commit-referenced issues via Gitea API (bug/feature/refactor). No code changes. Dedupes against open issues first.
2. hackmode-rage-worker — scheduled hourly-ish at :45 every 2h. RAGE implementer: picks highest-priority open issue/PR from nsaspy/hackmode, uses a DEDICATED GIT WORKTREE per issue/PR (user requirement), implements with gated verification, opens PR, auto-merges own work, closes the issue. Never leaves open issues behind. Receipts per steward conventions.

## Access Verification (confirmed 2026-09-04)
- Gitea API as mara: push+pull on nsaspy/hackmode: OK (27 open issues)
- mara/task-steward: OK (private, main)
- Scheduler tasks.json parses: OK (2 tasks)
