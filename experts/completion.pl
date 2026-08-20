:- module(expert_completion, [project_complete/1]).

:- use_module('../kb/generated/projects.pl').
:- use_module('../kb/evidence.pl').

project_complete(Project) :-
    completion_policy(Project, Gate),
    completion_gate(Project, Gate, satisfied),
    \+ blocking_failure(Project).
