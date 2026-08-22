:- module(expert_policy, [
    coding_freeze_active/0,
    coding_freeze_exception/1,
    hard_stop/1,
    project_execution_allowed/1
]).

:- use_module('../kb/generated/policies.pl').
:- use_module('../kb/generated/projects.pl').

coding_freeze_active :-
    policy_value([user_freeze, active], true),
    policy_value([scheduling, coding_freeze_overrides_scheduler], true).

coding_freeze_exception(Project) :-
    policy_value(
        [user_freeze, explicit_coding_exceptions, Project, protected_during_freeze],
        true
    ).

hard_stop(Project) :-
    policy_value([user_freeze, hard_stops, Project, implementation_allowed], false),
    policy_value([user_freeze, hard_stops, Project, automation_allowed], false).

project_execution_allowed(Project) :-
    project(Project),
    project_status_allows_execution(Project),
    \+ hard_stop(Project),
    freeze_allows_execution(Project).

project_status_allows_execution(Project) :-
    project_status(Project, active).
project_status_allows_execution(Project) :-
    project_status(Project, active_freeze_exception).

freeze_allows_execution(_Project) :-
    \+ coding_freeze_active,
    !.
freeze_allows_execution(Project) :-
    coding_freeze_exception(Project),
    !.
freeze_allows_execution(Project) :-
    project_mode(Project, permanent_non_coding).
