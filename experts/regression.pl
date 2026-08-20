:- module(expert_regression, [blocking_regression/1]).

:- use_module('../kb/evidence.pl').

blocking_regression(Task) :-
    regression(Task, Severity, _),
    memberchk(Severity, [critical, high]).
