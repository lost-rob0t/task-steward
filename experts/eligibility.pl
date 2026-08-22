:- module(expert_eligibility, [eligible_task/1]).

:- use_module('../kb/tasks.pl').
:- use_module('leases.pl').
:- use_module('policy.pl').

eligible_task(Task) :-
    task(Task),
    task_state(Task, open),
    task_project(Task, Project),
    project_execution_allowed(Project),
    \+ active_lease(Task, _, _).
