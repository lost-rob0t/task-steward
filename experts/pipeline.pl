:- module(expert_pipeline, [
    run_expert_pipeline/1,
    run_expert_pipeline/2,
    expert_execution/4
]).

:- use_module('registry.pl').

run_expert_pipeline(Executions) :-
    run_expert_pipeline(all, Executions).

run_expert_pipeline(Stage, Executions) :-
    findall(Order-Expert, runnable_expert(Stage, Expert, Order), Ordered0),
    keysort(Ordered0, Ordered),
    maplist(run_ordered_expert, Ordered, Executions).

runnable_expert(all, Expert, Order) :-
    expert_order(Expert, Order).
runnable_expert(Stage, Expert, Order) :-
    Stage \== all,
    expert_stage(Expert, Stage),
    expert_order(Expert, Order).

run_ordered_expert(Order-Expert, Execution) :-
    expert_stage(Expert, Stage),
    call_expert(Expert, Outcome),
    Execution = expert_execution(Expert, Stage, Order, Outcome).

call_expert(Expert, Outcome) :-
    current_predicate(Expert:expert_run/1),
    !,
    once(Expert:expert_run(Outcome)).
call_expert(Expert, Outcome) :-
    current_predicate(generated_project_rules:expert_run/2),
    generated_project_rules:expert_run(Expert, Outcome),
    !.
call_expert(_, no_op).

expert_execution(Expert, Stage, Order, Outcome) :-
    run_expert_pipeline(Executions),
    member(expert_execution(Expert, Stage, Order, Outcome), Executions).
