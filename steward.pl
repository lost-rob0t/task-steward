:- module(steward, [
    steward_validate/0,
    steward_evaluate/1,
    steward_evaluate_stage/2,
    steward_next/1,
    steward_next_external/2,
    steward_worker_decision/3,
    steward_explain/2,
    steward_status/1,
    steward_deployment_status/1,
    steward_lease_candidate/3,
    steward_lease_valid/3,
    steward_receipt_status/2
]).

:- use_module('kb/generated/projects.pl').
:- use_module('kb/generated/handoffs.pl').
:- use_module('kb/generated/policies.pl').
:- use_module('kb/generated/managed_github.pl').
:- use_module('kb/tasks.pl').
:- use_module('kb/evidence.pl').
:- use_module('kb/decisions.pl').

:- use_module('experts/registry.pl').
:- use_module('experts/pipeline.pl').
:- use_module('experts/leases.pl').
:- use_module('experts/policy.pl').
:- use_module('experts/eligibility.pl').
:- use_module('experts/dependencies.pl').
:- use_module('experts/failure.pl').
:- use_module('experts/regression.pl').
:- use_module('experts/priority.pl').
:- use_module('experts/skip_policy.pl').
:- use_module('experts/scheduling.pl').
:- use_module('experts/managed_github.pl').
:- use_module('experts/handoff.pl').
:- use_module('experts/completion.pl').
:- use_module('experts/receipts.pl').
:- use_module('experts/deployment.pl').
:- use_module('experts/generated/project_rules.pl').

steward_validate :-
    policy_version(_),
    policy_value([scheduling, authority], prolog),
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
    forall(project(Project), project_repo(Project, _)),
    forall((project(Project), Project \= task_stward_rage), (
        project_repo(Project, Repo),
        github_snapshot(Project, Repo, _, _),
        managed_worker_decision(Project, _, _)
    )),
    forall(handoff(Handoff, Source, Target), (
        handoff_status(Handoff, _),
        handoff_gate(Handoff, _),
        project(Source),
        project(Target)
    )),
    \+ deployment_requirement_unknown(_),
    forall(
        policy_member([expert_system_deployment, requires], Requirement),
        deployment_requirement_status(Requirement, _)
    ),
    forall(
        deployment_requirement_status(Requirement, satisfied),
        kb_generated_deployment:deployment_requirement_evidence(Requirement, _)
    ).

steward_evaluate(Executions) :-
    run_expert_pipeline(Executions).

steward_evaluate_stage(Stage, Executions) :-
    run_expert_pipeline(Stage, Executions).

steward_next(handoff(Handoff, Source, Target)) :-
    handoff_ready(Handoff),
    handoff(Handoff, Source, Target),
    !.
steward_next(external(Project, Ref)) :-
    steward_deployment_status(deployed),
    steward_next_external(Project, Ref),
    !.
steward_next(execute(Task)) :-
    next_task(Task),
    !.
steward_next(idle(no_schedulable_work)).

steward_next_external(Project, Ref) :-
    managed_next_external(Project, Ref).

steward_worker_decision(Project, Decision, Reason) :-
    managed_worker_decision(Project, Decision, Reason).

steward_explain(external(Project, Ref), explanation(external, Project, Ref, Score, Source, Snapshot)) :-
    managed_external_score(Project, Ref, Score),
    github_work_source(Project, Ref, Source),
    github_snapshot(Project, _, Snapshot, _).
steward_explain(worker(Project), explanation(worker, Project, Decision, Reason)) :-
    steward_worker_decision(Project, Decision, Reason).
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
steward_block_reason(Task, project_policy(Project, Reason)) :-
    task_project(Task, Project),
    project_execution_block_reason(Project, Reason).
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

steward_deployment_status(Status) :-
    expert_system_deployment_status(Status).

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
