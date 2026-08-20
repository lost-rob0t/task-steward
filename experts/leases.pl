:- module(expert_leases, [
    active_lease/3,
    next_generation/2,
    lease_candidate/3,
    valid_lease/3,
    stale_lease/3
]).

:- use_module('../kb/tasks.pl').

active_lease(Task, Generation, Owner) :-
    task_lease(Task, Generation, Owner, active),
    task_generation(Task, Generation).

next_generation(Task, Next) :-
    (   task_generation(Task, Current)
    ->  Next is Current + 1
    ;   Next = 1
    ).

lease_candidate(Task, Owner, Generation) :-
    task(Task),
    task_state(Task, open),
    \+ active_lease(Task, _, _),
    next_generation(Task, Generation),
    nonvar(Owner).

valid_lease(Task, Generation, Owner) :-
    active_lease(Task, Generation, Owner).

stale_lease(Task, Generation, Owner) :-
    task_lease(Task, Generation, Owner, active),
    task_generation(Task, Current),
    Generation < Current.
