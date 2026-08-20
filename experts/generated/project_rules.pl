% GENERATED FILE. DO NOT EDIT.
% Source: state/projects.yml inline Prolog blocks
:- module(generated_project_rules, []).

% project: prolog-rlm
production_ready(prolog_rlm) :-
    install_verified(prolog_rlm),
    full_suite_green(prolog_rlm),
    e2e_verified(prolog_rlm),
    persistence_recovery_verified(prolog_rlm),
    bounded_failure_verified(prolog_rlm),
    \+ p0_blocker(prolog_rlm),
    \+ p1_blocker(prolog_rlm).
