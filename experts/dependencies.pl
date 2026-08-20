:- module(expert_dependencies, [dependency_ready/1]).

:- use_module('../kb/tasks.pl').
:- use_module('eligibility.pl').

dependency_ready(Task) :-
    eligible_task(Task),
    forall(
        task_dependency(Task, Dependency),
        task_state(Dependency, completed)
    ).
