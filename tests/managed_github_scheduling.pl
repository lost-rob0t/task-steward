:- begin_tests(managed_github_scheduling).

:- use_module('../steward.pl').
:- use_module('../experts/managed_github.pl').
:- use_module('../kb/generated/managed_github.pl').

test(local_recall_hard_pause_wins_over_backlog_pressure) :-
    steward:steward_worker_decision(local_recall, pause, project_status(hard_paused_user)).

test(prolog_rlm_resumed_active_is_retained) :-
    steward:steward_worker_decision(prolog_rlm, keep, protected_project).

test(starintel_server_is_retained_by_authored_protection) :-
    steward:steward_worker_decision(starintel_server, keep, protected_project).

test(permanent_worker_is_retained_without_github_visibility) :-
    steward:steward_worker_decision(hourly_auto_dig, keep, permanent_worker).

test(fresh_unprotected_worker_without_schedulable_work_yields) :-
    expert_managed_github:worker_decision_from(active, rage, false, fresh, false, yield, no_schedulable_github_work).

test(fresh_unprotected_worker_with_schedulable_work_stays) :-
    expert_managed_github:worker_decision_from(active, rage, false, fresh, true, keep, schedulable_github_work).

test(partial_evidence_cannot_destructively_yield) :-
    expert_managed_github:worker_decision_from(active, rage, false, partial, false, keep, evidence_incomplete(partial)).

test(stale_evidence_cannot_destructively_yield) :-
    expert_managed_github:worker_decision_from(active, rage, false, stale, false, keep, evidence_incomplete(stale)).

test(missing_evidence_cannot_destructively_yield) :-
    expert_managed_github:worker_decision_from(active, rage, false, missing, false, keep, evidence_missing).

test(quiet_activity_is_not_an_abandonment_input) :-
    expert_managed_github:worker_decision_from(active, rage, false, fresh, true, keep, schedulable_github_work).

test(severity_changes_external_priority) :-
    expert_managed_github:external_score_from(100, issue, critical, not_applicable, not_applicable, Critical),
    expert_managed_github:external_score_from(100, issue, low, not_applicable, not_applicable, Low),
    Critical > Low.

test(unfinished_pr_repair_beats_equal_issue) :-
    expert_managed_github:external_score_from(100, pr, normal, failure, unknown, PullRequest),
    expert_managed_github:external_score_from(100, issue, normal, not_applicable, not_applicable, Issue),
    PullRequest > Issue.

test(partial_positive_evidence_can_select_known_actionable_work) :-
    steward:steward_next_external(hourly_auto_dig, pr_1958).

test(selected_external_work_has_exact_provenance) :-
    steward:steward_explain(
        external(hourly_auto_dig, pr_1958),
        explanation(external, hourly_auto_dig, pr_1958, _Score, 'github-pr:lost-rob0t/starintel-gpt-auto-dig#1958', partial)
    ).

test(known_pr_head_sha_survives_compilation) :-
    kb_generated_managed_github:github_work_head_sha(
        hourly_auto_dig,
        pr_1958,
        '3108063c512f519d1960e50f9634a7c940b85f28'
    ).

:- end_tests(managed_github_scheduling).
