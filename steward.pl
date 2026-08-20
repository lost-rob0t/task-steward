:- module(steward, [
    steward_validate/0,
    steward_next/1,
    steward_explain/2,
    steward_status/1
]).

:- use_module('kb/generated/projects.pl').
:- use_module('kb/handoffs.pl').
:- use_module('kb/tasks.pl').
:- use_module('kb/evidence.pl').

:- use_module('experts/registry.pl').
:- use_module('experts/eligibility.pl').
:- use_module('experts/dependencies.pl').
:- use_module('experts/failure.pl').
:- use_module('experts/regression.pl').
:- use_module('experts/priority.pl').
:- use_module('experts/skip_policy.pl').
:- use_module('experts/scheduling.pl').
:- use_module('experts/handoff.pl').
:- use_module('experts/completion.pl').

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
steward_explain(
    handoff(Handoff, Source, Target),
    explanation(Handoff, handoff_ready(Source, Target))
) :-
    handoff_ready(Handoff),
    handoff(Handoff, Source, Target).
steward_explain(idle(no_schedulable_work), explanation(no_schedulable_work)).

steward_status(status(Projects, Experts)) :-
    findall(project(Project, State, Mode), (
        project(Project),
        project_status(Project, State),
        project_mode(Project, Mode)
    ), Projects),
    findall(Order-Expert, expert_order(Expert, Order), Experts).
