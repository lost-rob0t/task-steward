% GENERATED FILE. DO NOT EDIT.
% Source: state/handoffs.yml inline Prolog blocks
:- module(generated_handoff_rules, [handoff_ready/1]).

:- use_module('../../kb/generated/projects.pl').
:- use_module('../../kb/evidence.pl').
:- multifile handoff_ready/1.

% handoff: infra-to-server
handoff_ready(infra_to_server) :-
    completion_gate(starintel_infra, automated_deployment_ready, satisfied),
    \+ blocking_failure(starintel_infra),
    project_status(starintel_server, waiting_handoff).
