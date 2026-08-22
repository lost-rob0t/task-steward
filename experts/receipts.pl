:- module(expert_receipts, [
    valid_decision_receipt/1,
    stale_decision_receipt/1,
    decision_receipt_explanation/2
]).

:- use_module('../kb/decisions.pl').
:- use_module('../kb/generated/handoffs.pl').
:- use_module('leases.pl').
:- use_module('skip_policy.pl').
:- use_module('handoff.pl').
:- use_module('completion.pl').

valid_decision_receipt(Id) :-
    decision_receipt(Id, execute, Task, Generation, Owner, Reason, Evidence),
    nonvar(Reason),
    nonvar(Evidence),
    valid_lease(Task, Generation, Owner).
valid_decision_receipt(Id) :-
    decision_receipt(Id, skip_job, job(Task, Job), 0, system, Reason, Evidence),
    nonvar(Reason),
    nonvar(Evidence),
    may_skip_job(Task, Job).
valid_decision_receipt(Id) :-
    decision_receipt(Id, skip_test, test(Task, Test), 0, system, Reason, Evidence),
    nonvar(Reason),
    nonvar(Evidence),
    may_skip_test(Task, Test).
valid_decision_receipt(Id) :-
    decision_receipt(Id, handoff, handoff(Handoff, Source, Target), 0, system, Reason, Evidence),
    nonvar(Reason),
    nonvar(Evidence),
    handoff(Handoff, Source, Target),
    handoff_ready(Handoff).
valid_decision_receipt(Id) :-
    decision_receipt(Id, complete, Project, 0, system, Reason, Evidence),
    nonvar(Reason),
    nonvar(Evidence),
    project_complete(Project).

stale_decision_receipt(Id) :-
    decision_receipt(Id, execute, Task, Generation, Owner, _Reason, _Evidence),
    stale_lease(Task, Generation, Owner).

receipt_basis(execute, Task, Generation, Owner, fenced_lease(Task, Generation, Owner)).
receipt_basis(skip_job, job(Task, Job), 0, system, skip_policy(job, Task, Job)).
receipt_basis(skip_test, test(Task, Test), 0, system, skip_policy(test, Task, Test)).
receipt_basis(handoff, handoff(Handoff, Source, Target), 0, system, handoff_gate(Handoff, Source, Target)).
receipt_basis(complete, Project, 0, system, completion_gate(Project)).

decision_receipt_explanation(
    Id,
    explanation(Action, Subject, Reason, Evidence, Basis)
) :-
    valid_decision_receipt(Id),
    decision_receipt(Id, Action, Subject, Generation, Owner, Reason, Evidence),
    receipt_basis(Action, Subject, Generation, Owner, Basis).
