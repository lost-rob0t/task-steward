:- module(expert_priority, [priority_component/4, priority_score/2]).

:- use_module('../kb/tasks.pl').
:- use_module('../kb/projects.pl').

priority_component(Task, explicit, Score, explicit_task_priority) :-
    task_priority(Task, Score).

priority_component(Task, project_base, Score, project_base_priority(Project)) :-
    task_project(Task, Project),
    base_priority(Project, Score).

priority_score(Task, Score) :-
    findall(Value, priority_component(Task, _, Value, _), Values),
    sum_list(Values, Score).
