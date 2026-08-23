:- begin_tests(freeze_eligibility).

:- use_module('../kb/tasks.pl').
:- use_module('../experts/eligibility.pl').
:- use_module('../experts/scheduling.pl').

reset_freeze_tasks :-
    retractall(kb_tasks:task(_)),
    retractall(kb_tasks:task_project(_, _)),
    retractall(kb_tasks:task_state(_, _)),
    retractall(kb_tasks:task_generation(_, _)),
    retractall(kb_tasks:task_lease(_, _, _, _)).

seed_open(Task, Project) :-
    assertz(kb_tasks:task(Task)),
    assertz(kb_tasks:task_project(Task, Project)),
    assertz(kb_tasks:task_state(Task, open)).

test(hard_stopped_prolog_rlm_is_not_eligible,
     [setup(reset_freeze_tasks), cleanup(reset_freeze_tasks), fail]) :-
    seed_open(frozen_prolog_task, prolog_rlm),
    expert_eligibility:eligible_task(frozen_prolog_task).

test(hard_stopped_prolog_rlm_is_not_schedulable,
     [setup(reset_freeze_tasks), cleanup(reset_freeze_tasks), fail]) :-
    seed_open(frozen_prolog_task, prolog_rlm),
    expert_scheduling:schedulable(frozen_prolog_task).

test(paused_infra_is_not_eligible,
     [setup(reset_freeze_tasks), cleanup(reset_freeze_tasks), fail]) :-
    seed_open(paused_infra_task, starintel_infra),
    expert_eligibility:eligible_task(paused_infra_task).

test(paused_infra_is_not_schedulable,
     [setup(reset_freeze_tasks), cleanup(reset_freeze_tasks), fail]) :-
    seed_open(paused_infra_task, starintel_infra),
    expert_scheduling:schedulable(paused_infra_task).

test(task_steward_is_eligible,
     [setup(reset_freeze_tasks), cleanup(reset_freeze_tasks)]) :-
    seed_open(steward_task, task_stward_rage),
    expert_eligibility:eligible_task(steward_task),
    expert_scheduling:schedulable(steward_task).

test(zara_is_eligible,
     [setup(reset_freeze_tasks), cleanup(reset_freeze_tasks)]) :-
    seed_open(zara_task, zara),
    expert_eligibility:eligible_task(zara_task),
    expert_scheduling:schedulable(zara_task).

test(hard_paused_local_recall_is_not_eligible,
     [setup(reset_freeze_tasks), cleanup(reset_freeze_tasks), fail]) :-
    seed_open(recall_task, local_recall),
    expert_eligibility:eligible_task(recall_task).

test(hard_paused_local_recall_is_not_schedulable,
     [setup(reset_freeze_tasks), cleanup(reset_freeze_tasks), fail]) :-
    seed_open(recall_task, local_recall),
    expert_scheduling:schedulable(recall_task).

test(primary_starintel_server_is_eligible,
     [setup(reset_freeze_tasks), cleanup(reset_freeze_tasks)]) :-
    seed_open(server_task, starintel_server),
    expert_eligibility:eligible_task(server_task),
    expert_scheduling:schedulable(server_task).

test(non_coding_auto_dig_remains_eligible,
     [setup(reset_freeze_tasks), cleanup(reset_freeze_tasks)]) :-
    seed_open(auto_dig_task, hourly_auto_dig),
    expert_eligibility:eligible_task(auto_dig_task),
    expert_scheduling:schedulable(auto_dig_task).

test(unknown_project_fails_closed,
     [setup(reset_freeze_tasks), cleanup(reset_freeze_tasks), fail]) :-
    seed_open(unknown_task, mystery_project),
    expert_scheduling:schedulable(unknown_task).

:- end_tests(freeze_eligibility).
