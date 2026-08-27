:- module(expert_workers, [
    worker_dispatch_from/3,
    worker_dispatchable/3,
    worker_dispatch_block_reason/3,
    runtime_generation_valid/2
]).

:- use_module('../kb/generated/workers.pl').
:- use_module('managed_github.pl').

worker_dispatch_from(true, keep, dispatchable) :- !.
worker_dispatch_from(false, _Decision, blocked(worker_disabled)) :- !.
worker_dispatch_from(true, Decision, blocked(project_decision(Decision))) :-
    Decision \= keep.

worker_dispatchable(Worker, Project, Reason) :-
    worker(Worker),
    worker_enabled(Worker),
    worker_project(Worker, Project),
    managed_worker_decision(Project, keep, Reason).

worker_dispatch_block_reason(Worker, _Project, worker_disabled) :-
    worker(Worker),
    worker_disabled(Worker),
    !.
worker_dispatch_block_reason(Worker, Project, wrong_project(Expected)) :-
    worker(Worker),
    worker_project(Worker, Expected),
    Expected \= Project,
    !.
worker_dispatch_block_reason(Worker, Project, project_decision(Decision, Reason)) :-
    worker(Worker),
    worker_project(Worker, Project),
    managed_worker_decision(Project, Decision, Reason),
    Decision \= keep.

runtime_generation_valid(Current, Presented) :-
    integer(Current),
    integer(Presented),
    Current =:= Presented.
