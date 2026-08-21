:- begin_tests(regressions).

:- use_module('../experts/regression.pl').
:- use_module('../kb/evidence.pl').

reset_evidence :-
    retractall(kb_evidence:ci_status(_, _, _)),
    retractall(kb_evidence:regression(_, _, _)).

test(skipped_known_good_job_blocks, [setup(reset_evidence), cleanup(reset_evidence)]) :-
    assertz(kb_evidence:ci_status(task_a, required_tests, known_good)),
    assertz(kb_evidence:ci_status(task_a, required_tests, skipped)),
    expert_regression:derived_regression(task_a, high, required_job_skipped(required_tests)),
    expert_regression:blocking_regression(task_a).

test(missing_known_good_job_blocks, [setup(reset_evidence), cleanup(reset_evidence)]) :-
    assertz(kb_evidence:ci_status(task_a, required_tests, known_good)),
    assertz(kb_evidence:ci_status(task_a, required_tests, missing)),
    expert_regression:derived_regression(task_a, high, required_job_missing(required_tests)),
    expert_regression:blocking_regression(task_a).

test(failed_known_good_job_is_critical, [setup(reset_evidence), cleanup(reset_evidence)]) :-
    assertz(kb_evidence:ci_status(task_a, required_tests, known_good)),
    assertz(kb_evidence:ci_status(task_a, required_tests, failed)),
    expert_regression:derived_regression(task_a, critical, required_job_failed(required_tests)).

test(ordinary_success_does_not_block, [setup(reset_evidence), cleanup(reset_evidence), fail]) :-
    assertz(kb_evidence:ci_status(task_a, required_tests, success)),
    expert_regression:blocking_regression(task_a).

test(explicit_low_regression_does_not_block, [setup(reset_evidence), cleanup(reset_evidence), fail]) :-
    assertz(kb_evidence:regression(task_a, low, cosmetic_change)),
    expert_regression:blocking_regression(task_a).

:- end_tests(regressions).
