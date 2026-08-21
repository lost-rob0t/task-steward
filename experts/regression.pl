:- module(expert_regression, [blocking_regression/1, derived_regression/3]).

:- use_module('../kb/evidence.pl').

% Explicit mirrored regressions remain authoritative evidence.
derived_regression(Task, Severity, Reason) :-
    regression(Task, Severity, Reason).

% A required CI job that was known-good and is now skipped is a false green.
derived_regression(Task, high, required_job_skipped(Job)) :-
    ci_status(Task, Job, known_good),
    ci_status(Task, Job, skipped).

% A required CI job that was known-good and disappears is suspicious, not success.
derived_regression(Task, high, required_job_missing(Job)) :-
    ci_status(Task, Job, known_good),
    ci_status(Task, Job, missing).

% A required CI job that regresses from known-good to failure blocks scheduling.
derived_regression(Task, critical, required_job_failed(Job)) :-
    ci_status(Task, Job, known_good),
    ci_status(Task, Job, failed).

blocking_regression(Task) :-
    derived_regression(Task, Severity, _),
    memberchk(Severity, [critical, high]).
