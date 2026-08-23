:- module(expert_managed_github, [
    managed_worker_decision/3,
    managed_next_external/2,
    managed_external_score/3,
    worker_decision_from/7,
    external_score_from/6
]).

:- use_module('../kb/generated/projects.pl').
:- use_module('../kb/generated/managed_github.pl').
:- use_module('policy.pl').

active_status(active).
active_status(active_freeze_exception).

% Pure decision seam used by regressions. Incomplete evidence is never authority
% for a destructive yield; explicit user/project stops always win.
worker_decision_from(Status, _Mode, _Protected, _Snapshot, _HasWork, pause, project_status(Status)) :-
    memberchk(Status, [hard_paused_user, hard_stopped_user, paused_user, paused]),
    !.
worker_decision_from(Status, permanent_worker, _Protected, _Snapshot, _HasWork, keep, permanent_worker) :-
    active_status(Status),
    !.
worker_decision_from(Status, _Mode, true, _Snapshot, _HasWork, keep, protected_project) :-
    active_status(Status),
    !.
worker_decision_from(Status, _Mode, false, missing, _HasWork, keep, evidence_missing) :-
    active_status(Status),
    !.
worker_decision_from(Status, _Mode, false, Snapshot, _HasWork, keep, evidence_incomplete(Snapshot)) :-
    active_status(Status),
    memberchk(Snapshot, [partial, stale, unavailable]),
    !.
worker_decision_from(Status, _Mode, false, fresh, true, keep, schedulable_github_work) :-
    active_status(Status),
    !.
worker_decision_from(Status, _Mode, false, fresh, false, yield, no_schedulable_github_work) :-
    active_status(Status).

managed_worker_decision(Project, Decision, Reason) :-
    project(Project),
    project_status(Project, Status),
    project_mode(Project, Mode),
    ( protected_project(Project) -> Protected = true ; Protected = false ),
    ( github_snapshot(Project, _, Snapshot, _) -> true ; Snapshot = missing ),
    ( managed_retaining_work(Project, _) -> HasWork = true ; HasWork = false ),
    worker_decision_from(Status, Mode, Protected, Snapshot, HasWork, Decision, Reason),
    !.

managed_retaining_work(Project, Ref) :-
    github_work(Project, Ref),
    github_work_state(Project, Ref, open),
    github_work_kind(Project, Ref, pr),
    !.
managed_retaining_work(Project, Ref) :-
    github_work(Project, Ref),
    github_work_state(Project, Ref, open),
    github_work_kind(Project, Ref, Kind),
    memberchk(Kind, [issue, followup]),
    github_work_readiness(Project, Ref, Readiness),
    memberchk(Readiness, [ready, pending]).

trusted_positive_snapshot(Project) :-
    github_snapshot(Project, _, State, _),
    memberchk(State, [fresh, partial]).

managed_external_candidate(Project, Ref) :-
    project_execution_allowed(Project),
    trusted_positive_snapshot(Project),
    github_work(Project, Ref),
    github_work_state(Project, Ref, open),
    github_work_readiness(Project, Ref, ready),
    github_work_kind(Project, Ref, Kind),
    actionable_kind(Project, Ref, Kind).

actionable_kind(Project, Ref, pr) :-
    github_work_ci(Project, Ref, Ci),
    Ci \= pending.
actionable_kind(_Project, _Ref, issue).
actionable_kind(_Project, _Ref, followup).

severity_weight(critical, 400).
severity_weight(high, 300).
severity_weight(normal, 200).
severity_weight(low, 100).

kind_weight(pr, 60).
kind_weight(followup, 40).
kind_weight(issue, 20).

ci_weight(failure, 30).
ci_weight(success, 20).
ci_weight(unknown, 10).
ci_weight(not_applicable, 0).
ci_weight(pending, -1000).

review_weight(blocked, 20).
review_weight(clean, 10).
review_weight(unknown, 5).
review_weight(not_applicable, 0).
review_weight(pending, -10).

external_score_from(Base, Kind, Severity, Ci, Review, Score) :-
    severity_weight(Severity, SeverityWeight),
    kind_weight(Kind, KindWeight),
    ci_weight(Ci, CiWeight),
    review_weight(Review, ReviewWeight),
    Score is Base + SeverityWeight + KindWeight + CiWeight + ReviewWeight.

managed_external_score(Project, Ref, Score) :-
    managed_external_candidate(Project, Ref),
    base_priority(Project, Base),
    github_work_severity(Project, Ref, Severity),
    github_work_kind(Project, Ref, Kind),
    github_work_ci(Project, Ref, Ci),
    github_work_review(Project, Ref, Review),
    external_score_from(Base, Kind, Severity, Ci, Review, Score).

managed_next_external(Project, Ref) :-
    managed_external_score(Project, Ref, Score),
    \+ (
        managed_external_score(OtherProject, OtherRef, OtherScore),
        external_candidate_better(OtherProject, OtherRef, OtherScore, Project, Ref, Score)
    ).

external_candidate_better(_P1, _R1, Score1, _P2, _R2, Score2) :-
    Score1 > Score2,
    !.
external_candidate_better(P1, R1, Score, P2, R2, Score) :-
    P1-R1 @< P2-R2.
