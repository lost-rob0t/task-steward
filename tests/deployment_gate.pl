:- begin_tests(deployment_gate).

:- use_module('../experts/deployment.pl').
:- use_module('../kb/generated/projects.pl').
:- use_module('../kb/generated/tasks.pl').


test(current_state_is_deployed) :-
    expert_system_deployed.

test(current_deployment_status_is_deployed) :-
    expert_system_deployment_status(deployed).

test(deployed_steward_uses_post_deployment_mode) :-
    kb_generated_projects:project_mode(task_stward_rage, deployed_scheduling_self_rage_fallback),
    \+ kb_generated_projects:project_mode(task_stward_rage, self_rage_building_experts).

test(deployment_epic_is_no_longer_schedulable_as_open_work) :-
    kb_generated_tasks:task_state(task_stward_rage_issue_1, closed),
    \+ kb_generated_tasks:task_state(task_stward_rage_issue_1, open).

test(policy_requirements_have_exactly_one_status) :-
    forall(
        kb_generated_policies:policy_member([expert_system_deployment, requires], Requirement),
        aggregate_all(count, kb_generated_deployment:deployment_requirement(Requirement, _), 1)
    ).

test(no_unknown_deployment_requirement) :-
    \+ deployment_requirement_unknown(_).

test(no_missing_deployment_requirement) :-
    \+ deployment_requirement_missing(_).

test(satisfied_requirements_have_evidence) :-
    forall(
        deployment_requirement_status(Requirement, satisfied),
        kb_generated_deployment:deployment_requirement_evidence(Requirement, _)
    ).

:- end_tests(deployment_gate).
