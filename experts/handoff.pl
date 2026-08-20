:- module(expert_handoff, [handoff_ready/1]).

:- use_module('../kb/handoffs.pl').
:- use_module('../kb/generated/projects.pl').
:- use_module('../kb/evidence.pl').

handoff_ready(Handoff) :-
    handoff(Handoff, Source, Target),
    handoff_status(Handoff, armed),
    handoff_gate(Handoff, Gate),
    completion_gate(Source, Gate, satisfied),
    project_status(Target, waiting_handoff),
    \+ blocking_failure(Source).
