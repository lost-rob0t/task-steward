:- module(expert_registry, [
    expert/1,
    expert_stage/2,
    expert_order/2,
    expert_dependency/2
]).

:- use_module('generated/registry.pl').

builtin_expert(leases, eligibility, 5).
builtin_expert(eligibility, eligibility, 10).
builtin_expert(dependencies, dependencies, 20).
builtin_expert(failure, failure, 30).
builtin_expert(regression, regression, 40).
builtin_expert(priority, priority, 50).
builtin_expert(skip_policy, skip_policy, 60).
builtin_expert(scheduling, scheduling, 70).
builtin_expert(handoff, handoff, 80).
builtin_expert(completion, completion, 90).
builtin_expert(receipts, completion, 95).

builtin_dependency(eligibility, leases).
builtin_dependency(receipts, completion).

expert(Name) :-
    builtin_expert(Name, _, _).
expert(Name) :-
    custom_expert(Name).

expert_stage(Name, Stage) :-
    builtin_expert(Name, Stage, _).
expert_stage(Name, Stage) :-
    custom_expert_stage(Name, Stage).

expert_order(Name, Order) :-
    builtin_expert(Name, _, Order).
expert_order(Name, Order) :-
    custom_expert_order(Name, Order).

expert_dependency(Name, Dependency) :-
    builtin_dependency(Name, Dependency).
expert_dependency(Name, Dependency) :-
    custom_expert_dependency(Name, Dependency).
