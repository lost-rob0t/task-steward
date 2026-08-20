:- module(expert_scheduling, [schedulable/1, next_task/1]).

:- use_module('dependencies.pl').
:- use_module('regression.pl').
:- use_module('priority.pl').

schedulable(Task) :-
    dependency_ready(Task),
    \+ blocking_regression(Task).

next_task(Task) :-
    schedulable(Task),
    priority_score(Task, Score),
    \+ (
        schedulable(Other),
        Other \= Task,
        priority_score(Other, OtherScore),
        OtherScore > Score
    ).
