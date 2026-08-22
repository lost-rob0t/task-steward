:- module(expert_skip_policy, [
    may_skip_job/2,
    may_skip_test/2,
    skip_job_explanation/3,
    skip_test_explanation/3
]).

:- multifile mandatory_job/1.
:- multifile mandatory_test/1.
:- multifile job_irrelevant/2.
:- multifile test_irrelevant/2.

:- dynamic mandatory_job/1.
:- dynamic mandatory_test/1.
:- dynamic job_irrelevant/2.
:- dynamic test_irrelevant/2.

may_skip_job(Task, Job) :-
    job_irrelevant(Task, Job),
    \+ mandatory_job(Job).

may_skip_test(Task, Test) :-
    test_irrelevant(Task, Test),
    \+ mandatory_test(Test).

skip_job_explanation(
    Task,
    Job,
    skip_policy(job_irrelevant(Task, Job), non_mandatory(Job))
) :-
    may_skip_job(Task, Job).

skip_test_explanation(
    Task,
    Test,
    skip_policy(test_irrelevant(Task, Test), non_mandatory(Test))
) :-
    may_skip_test(Task, Test).
