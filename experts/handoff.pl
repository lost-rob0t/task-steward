:- module(expert_handoff, [handoff_ready/1]).

:- use_module('../kb/generated/handoffs.pl').
:- use_module('../kb/generated/projects.pl').
:- use_module('../kb/evidence.pl').
:- use_module('generated/handoff_rules.pl', []).

handoff_ready(Handoff) :-
    handoff(Handoff, Source, Target),
    handoff_status(Handoff, armed),
    handoff_gate(Handoff, Gate),
    completion_gate(Source, Gate, satisfied),
    project_status(Target, waiting_handoff),
    \+ blocking_failure(Source),
    custom_handoff_rule_allows(Handoff).

custom_handoff_rule_allows(Handoff) :-
    generated_handoff_rules:handoff_ready(Handoff),
    !.
custom_handoff_rule_allows(Handoff) :-
    \+ clause(generated_handoff_rules:handoff_ready(Handoff), _).
