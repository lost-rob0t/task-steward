:- module(kb_evidence, [
    run_result/2,
    run_failure/3,
    ci_status/3,
    regression/3,
    completion_gate/3,
    blocking_failure/1,
    observed_at/2
]).

:- dynamic run_result/2.
:- dynamic run_failure/3.
:- dynamic ci_status/3.
:- dynamic regression/3.
:- dynamic completion_gate/3.
:- dynamic blocking_failure/1.
:- dynamic observed_at/2.

% These predicates hold mirrored evidence observed by the Task Steward.
% Never infer success from absence of a failure fact.
