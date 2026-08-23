:- begin_tests(scheduling_modes).

:- use_module('../experts/scheduling.pl').
:- use_module('../kb/tasks.pl').

reset_tasks :-
    retractall(kb_tasks:task(_)),
    retractall(kb_tasks:task_project(_, _)),
    retractall(kb_tasks:task_source(_, _)),
    retractall(kb_tasks:task_state(_, _)),
    retractall(kb_tasks:task_priority(_, _)),
    retractall(kb_tasks:task_dependency(_, _)).

seed_ready(Task, Project, Priority) :-
    assertz(kb_tasks:task(Task)),
    assertz(kb_tasks:task_project(Task, Project)),
    assertz(kb_tasks:task_state(Task, open)),
    assertz(kb_tasks:task_priority(Task, Priority)).

test(postdeployment_staged_self_close_leaves_no_self_rage_issue) :-
    \+ schedulable(task_stward_rage_issue_42),
    \+ schedulable(task_stward_rage_issue_40),
    \+ schedulable(task_stward_rage_issue_38),
    \+ schedulable(task_stward_rage_issue_36),
    \+ schedulable(task_stward_rage_issue_34),
    \+ schedulable(task_stward_rage_issue_32),
    \+ schedulable(task_stward_rage_issue_30),
    \+ schedulable(task_stward_rage_issue_28),
    \+ schedulable(task_stward_rage_issue_26),
    \+ steward_mode_next(deployed, none, _).

test(predeployment_self_rage_even_with_external_work,
     [setup(reset_tasks), cleanup(reset_tasks)]) :-
    seed_ready(external_issue, zara, 100),
    seed_ready(steward_issue, task_stward_rage, 1),
    steward_mode_next(building, external_issue, steward_issue).

test(postdeployment_external_work_wins,
     [setup(reset_tasks), cleanup(reset_tasks)]) :-
    seed_ready(external_issue, zara, 100),
    seed_ready(steward_issue, task_stward_rage, 1),
    steward_mode_next(deployed, external_issue, external_issue).

test(postdeployment_self_rage_only_when_idle,
     [setup(reset_tasks), cleanup(reset_tasks)]) :-
    seed_ready(steward_issue, task_stward_rage, 1),
    steward_mode_next(deployed, none, steward_issue).

test(quiet_period_does_not_abandon_active_project,
     [setup(reset_tasks), cleanup(reset_tasks)]) :-
    seed_ready(quiet_issue, zara, 10),
    assertz(kb_tasks:task_source(quiet_issue, quiet_period)),
    schedulable(quiet_issue).

:- end_tests(scheduling_modes).
