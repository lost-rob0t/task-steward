:- module(expert_receipts, [
    valid_decision_receipt/1,
    stale_decision_receipt/1
]).

:- use_module('../kb/decisions.pl').
:- use_module('leases.pl').

valid_decision_receipt(Id) :-
    decision_receipt(Id, execute, Task, Generation, Owner, Reason, Evidence),
    nonvar(Reason),
    nonvar(Evidence),
    valid_lease(Task, Generation, Owner).
valid_decision_receipt(Id) :-
    decision_receipt(Id, Action, _Subject, 0, system, Reason, Evidence),
    Action \= execute,
    nonvar(Reason),
    nonvar(Evidence).

stale_decision_receipt(Id) :-
    decision_receipt(Id, execute, Task, Generation, Owner, _Reason, _Evidence),
    stale_lease(Task, Generation, Owner).
