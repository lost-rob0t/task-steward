:- begin_tests(failure_signatures).

:- use_module('../experts/failure.pl').
:- use_module('../kb/evidence.pl').

clear_failures :-
    retractall(kb_evidence:run_failure(_, _, _)).

test(same_failure_has_same_signature_across_runs, [setup(clear_failures), cleanup(clear_failures)]) :-
    assertz(kb_evidence:run_failure(run_1, timeout, provider_unavailable)),
    assertz(kb_evidence:run_failure(run_2, timeout, provider_unavailable)),
    failure_signature(run_1, A),
    failure_signature(run_2, B),
    assertion(A == B).

test(different_detail_changes_signature, [setup(clear_failures), cleanup(clear_failures)]) :-
    assertz(kb_evidence:run_failure(run_1, test, suite_a)),
    assertz(kb_evidence:run_failure(run_2, test, suite_b)),
    failure_signature(run_1, A),
    failure_signature(run_2, B),
    assertion(A \== B).

test(transient_failure_retries, [setup(clear_failures), cleanup(clear_failures)]) :-
    assertz(kb_evidence:run_failure(run_1, rate_limit, provider_429)),
    assertion(retry_class(run_1, retry)).

test(deterministic_failure_stops, [setup(clear_failures), cleanup(clear_failures)]) :-
    assertz(kb_evidence:run_failure(run_1, test, assertion_failed)),
    assertion(retry_class(run_1, stop)).

test(unclassified_failure_is_fail_closed_unknown, [setup(clear_failures), cleanup(clear_failures)]) :-
    assertz(kb_evidence:run_failure(run_1, mystery, strange_failure)),
    assertion(retry_class(run_1, unknown)),
    assertion(\+ retryable_failure(run_1)).

:- end_tests(failure_signatures).

:- initialization(main, main).
main :- run_tests, halt.
