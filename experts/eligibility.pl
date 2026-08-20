:- module(expert_eligibility, [eligible_task/1]).

:- use_module('../kb/tasks.pl').

eligible_task(Task) :-
    task(Task),
    task_state(Task, open),
    \+ task_lease(Task, _, _).
