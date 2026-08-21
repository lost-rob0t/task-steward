:- module(expert_scheduling, [schedulable/1, next_task/1, steward_mode_next/3]).

:- use_module('dependencies.pl').
:- use_module('regression.pl').
:- use_module('priority.pl').
:- use_module('../kb/tasks.pl').

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

% Before deployment, reconciliation may identify an external candidate, but the
% steward's remaining work is always its own highest-priority schedulable Issue.
steward_mode_next(Status, _ExternalCandidate, Task) :-
    Status \= deployed,
    self_rage_task(Task),
    !.
% Once deployed, normal scheduling is primary whenever external work exists.
steward_mode_next(deployed, ExternalCandidate, ExternalCandidate) :-
    ExternalCandidate \= none,
    schedulable(ExternalCandidate),
    !.
% Only a genuinely idle deployed scheduler falls back to steward self-RAGE.
steward_mode_next(deployed, none, Task) :-
    self_rage_task(Task).

self_rage_task(Task) :-
    schedulable(Task),
    kb_tasks:task_project(Task, task_stward_rage),
    priority_score(Task, Score),
    \+ (
        schedulable(Other),
        Other \= Task,
        kb_tasks:task_project(Other, task_stward_rage),
        priority_score(Other, OtherScore),
        OtherScore > Score
    ).
