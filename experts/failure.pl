:- module(expert_failure, [retryable_failure/1, deterministic_failure/1]).

:- use_module('../kb/evidence.pl').

retryable_failure(Run) :-
    run_failure(Run, Class, _),
    memberchk(Class, [timeout, infrastructure, rate_limit, transient]).

deterministic_failure(Run) :-
    run_failure(Run, Class, _),
    memberchk(Class, [build, test, lint, typecheck, packaging, policy, regression]).
