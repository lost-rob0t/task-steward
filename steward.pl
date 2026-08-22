:- module(steward, [
    steward_validate/0,
    steward_evaluate/1,
    steward_evaluate_stage/2,
    steward_next/1,
    steward_explain/2,
    steward_status/1,
    steward_lease_candidate/3,
    steward_lease_valid/3,
    steward_receipt_status/2
]).

:- use_module('kb/generated/projects.pl').
:- use_module('kb/handoffs.pl').
:- use_module('kb/tasks.pl').
:- use_module('kb/evidence.pl').
:- use_module('kb/decisions.pl').

:- use_module('experts/registry.pl').
:- use_module('experts/pipeline.pl').
:- use_module('experts/leases.pl').
:- use_module('experts/eligibility.pl').
:- use_module('experts/dependencies.pl').
:- use_module('experts/failure.pl').
:- use_module('experts/regression.pl').
:- use_module('experts/priority.pl').
:- use_module('experts/skip_policy.pl').
:- use_module('experts/scheduling.pl').
:- use_module('experts/handoff.pl').
:- use_module('experts/completion.pl').
:- use_module('experts/receipts.pl').
:- use_module('experts/generated/project_rules.pl').

steward_validate :-
    findall(Order-Expert, expert_order(Expert, Order), Ordered),
    sort(Ordered, Sorted),
    length(Ordered, Count),
    length(Sorted, Count),
    forall(expert(Expert), (expert_stage(Expert, _), expert_order(Expert, _))),
    forall(expert_dependency(Expert, Dependency), (
        expert(Expert),
        expert(Dependency),
        expert_order(Dependency, DependencyOrder),
        expert_order(Expert, ExpertOrder),
        DependencyOrder < ExpertOrder
    )),
    forall(project(Project), project_repo(Project, _)).

steward_evaluate(Executions) :-
    run_expert_pipeline(Executions).

steward_evaluate_stage(Stage, Executions) :-
    run_expert_pipeline(Stage, Executions).

steward_next(handoff(Handoff, Source, Target)) :-
    handoff_ready(Handoff),
    handoff(Handoff, Source, Target),
    !.
steward_next(execute(Task)) :-
    next_task(Task),
    !.
steward_next(idle(no_schedulable_work)).

steward_explain(execute(Task), explanation(Task, Score, Components)) :-
    priority_score(Task, Score),
    findall(
        component(Name, Value, Reason),
        priority_component(Task, Name, Value, Reason),
        Components
    ).
steward_explain(blocked(Task), explanation(Task, blocked, Reasons)) :-
    task(Task),
    findall(Reason, steward_block_reason(Task, Reason), RawReasons),
    sort(RawReasons, Reasons),
    Reasons \= [].
steward_explain(
    skip_job(Task, Job),
    explanation(skip_job, job(Task, Job), Basis)
) :-
    skip_job_explanation(Task, Job, Basis).
steward_explain(
    skip_test(Task, Test),
    explanation(skip_test, test(Task, Test), Basis)
) :-
    skip_test_explanation(Task, Test, Basis).
steward_explain(
    handoff(Handoff, Source, Target),
    explanation(Handoff, handoff_ready(Source, Target))
) :-
    handoff_ready(Handoff),
    handoff(Handoff, Source, Target).
steward_explain(receipt(Id), Explanation) :-
    decision_receipt_explanation(Id, Explanation).
steward_explain(idle(no_schedulable_work), explanation(no_schedulable_work)).

steward_block_reason(Task, task_state(State)) :-
    task_state(Task, State),
    State \= open.
steward_block_reason(Task, active_lease(Generation, Owner)) :-
    active_lease(Task, Generation, Owner).
steward_block_reason(Task, dependency_not_completed(Dependency, State)) :-
    task_dependency(Task, Dependency),
    task_state(Dependency, State),
    State \= completed.
steward_block_reason(Task, dependency_not_completed(Dependency, missing_state)) :-
    task_dependency(Task, Dependency),
    \+ task_state(Dependency, _).
steward_block_reason(Task, blocking_regression(Severity, Reason)) :-
    derived_regression(Task, Severity, Reason),
    memberchk(Severity, [high, critical]).

steward_lease_candidate(Task, Owner, Generation) :-
    lease_candidate(Task, Owner, Generation).

steward_lease_valid(Task, Generation, Owner) :-
    valid_lease(Task, Generation, Owner).

steward_receipt_status(Id, valid) :-
    valid_decision_receipt(Id),
    !.
steward_receipt_status(Id, stale) :-
    stale_decision_receipt(Id),
    !.
steward_receipt_status(Id, invalid) :-
    decision_receipt(Id, _, _, _, _, _, _).

steward_status(status(Projects, Experts)) :-
    findall(project(Project, State, Mode), (
        project(Project),
        project_status(Project, State),
        project_mode(Project, Mode)
    ), Projects),
    findall(Order-Expert, expert_order(Expert, Order), Experts).
