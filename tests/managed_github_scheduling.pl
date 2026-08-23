:- begin_tests(managed_github_scheduling).

:- use_module('../steward.pl').

test(managed_worker_decision_is_exposed) :-
    steward:steward_worker_decision(starintel_server, keep, _).

test(managed_next_external_is_exposed) :-
    steward:steward_next_external(_, _).

:- end_tests(managed_github_scheduling).
