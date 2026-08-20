:- module(kb_tasks, [
    task/1,
    task_project/2,
    task_source/2,
    task_state/2,
    task_priority/2,
    task_dependency/2,
    task_generation/2,
    task_lease/4
]).

:- dynamic task/1.
:- dynamic task_project/2.
:- dynamic task_source/2.
:- dynamic task_state/2.
:- dynamic task_priority/2.
:- dynamic task_dependency/2.
:- dynamic task_generation/2.
:- dynamic task_lease/4.

% GitHub Issues in their owning repositories are canonical tasks.
% The Task Steward mirrors only scheduling facts here.
%
% task_generation(Task, Generation) is the highest generation durably observed
% for the task. task_lease(Task, Generation, Owner, State) records ownership for
% exactly that generation. A later generation fences every earlier owner.
