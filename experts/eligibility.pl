:- module(expert_eligibility, [eligible_task/1]).

:- use_module('../kb/tasks.pl').
:- use_module('leases.pl').

eligible_task(Task) :-
    task(Task),
    task_state(Task, open),
    \+ active_lease(Task, _, _).
