:- module(expert_deployment, [
    deployment_requirement_status/2,
    deployment_requirement_missing/1,
    deployment_requirement_unknown/1,
    expert_system_deployed/0,
    expert_system_deployment_status/1
]).

:- use_module('../kb/generated/policies.pl').
:- use_module('../kb/generated/deployment.pl').

deployment_requirement_status(Requirement, Status) :-
    policy_member([expert_system_deployment, requires], Requirement),
    deployment_requirement(Requirement, Status).

deployment_requirement_missing(Requirement) :-
    policy_member([expert_system_deployment, requires], Requirement),
    \+ deployment_requirement(Requirement, satisfied).

deployment_requirement_unknown(Requirement) :-
    deployment_requirement(Requirement, _),
    \+ policy_member([expert_system_deployment, requires], Requirement).

expert_system_deployed :-
    \+ deployment_requirement_missing(_),
    \+ deployment_requirement_unknown(_),
    forall(
        policy_member([expert_system_deployment, requires], Requirement),
        deployment_requirement_evidence(Requirement, _)
    ).

expert_system_deployment_status(deployed) :-
    expert_system_deployed,
    !.
expert_system_deployment_status(building(Missing)) :-
    findall(Requirement, deployment_requirement_missing(Requirement), Raw),
    sort(Raw, Missing).
