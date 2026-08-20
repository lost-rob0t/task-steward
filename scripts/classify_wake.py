#!/usr/bin/env python3
"""Classify whether a workflow event may execute steward evaluation.

Validation runs for every configured workflow event. Logical steward evaluation is
narrower: explicit steward wake commits and manual dispatches may evaluate;
PR validation, ordinary pushes, and state-maintenance commits may not.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass

WAKE_MARKER = "[steward-wake]"
STATE_MARKER = "[steward-state]"
ALLOWED_EVENTS = frozenset({"push", "pull_request", "workflow_dispatch"})


@dataclass(frozen=True)
class WakeDecision:
    evaluate: bool
    reason: str


def classify(event: str, message: str = "") -> WakeDecision:
    if event not in ALLOWED_EVENTS:
        raise ValueError(f"unsupported workflow event: {event}")

    has_wake = WAKE_MARKER in message
    has_state = STATE_MARKER in message
    if has_wake and has_state:
        raise ValueError("commit must not contain both steward wake and state markers")

    if event == "workflow_dispatch":
        return WakeDecision(True, "manual_dispatch")
    if event == "pull_request":
        return WakeDecision(False, "pull_request_validation_only")
    if has_state:
        return WakeDecision(False, "self_generated_state_commit")
    if has_wake:
        return WakeDecision(True, "explicit_steward_wake")
    return WakeDecision(False, "ordinary_push_validation_only")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True, choices=sorted(ALLOWED_EVENTS))
    parser.add_argument("--message", default="")
    args = parser.parse_args()

    decision = classify(args.event, args.message)
    print(f"evaluate={'true' if decision.evaluate else 'false'}")
    print(f"reason={decision.reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
