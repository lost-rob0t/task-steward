:- module(expert_skip_policy, [may_skip_job/2, may_skip_test/2]).

:- multifile mandatory_job/1.
:- multifile mandatory_test/1.
:- multifile job_irrelevant/2.
:- multifile test_irrelevant/2.

may_skip_job(Task, Job) :-
    job_irrelevant(Task, Job),
    \+ mandatory_job(Job).

may_skip_test(Task, Test) :-
    test_irrelevant(Task, Test),
    \+ mandatory_test(Test).
