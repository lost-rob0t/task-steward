% GENERATED FILE. DO NOT EDIT.
% Source: state/handoffs.yml
:- module(kb_generated_handoffs, [
    handoff/3,
    handoff_status/2,
    handoff_gate/2,
    handoff_requirement/2
]).

handoff(infra_to_server, starintel_infra, starintel_server).
handoff_status(infra_to_server, armed).
handoff_gate(infra_to_server, automated_deployment_ready).
handoff_requirement(infra_to_server, reproducible_builds).
handoff_requirement(infra_to_server, automated_apply_verified).
handoff_requirement(infra_to_server, rollback_recovery_verified).
handoff_requirement(infra_to_server, secrets_externalized).
handoff_requirement(infra_to_server, required_ci_green).
handoff_requirement(infra_to_server, no_p0_p1_deployment_blockers).
