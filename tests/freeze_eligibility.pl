:- begin_tests(freeze_eligibility).

:- use_module('../kb/tasks.pl').
:- use_module('../experts/eligibility.pl').

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

test(frozen_infra_is_not_eligible,
     [setup(reset_freeze_tasks), cleanup(reset_freeze_tasks), fail]) :-
    seed_open(frozen_infra_task, starintel_infra),
    expert_eligibility:eligible_task(frozen_infra_task).

test(task_steward_freeze_exception_is_eligible,
     [setup(reset_freeze_tasks), cleanup(reset_freeze_tasks)]) :-
    seed_open(steward_task, task_stward_rage),
    expert_eligibility:eligible_task(steward_task).

test(zara_freeze_exception_is_eligible,
     [setup(reset_freeze_tasks), cleanup(reset_freeze_tasks)]) :-
    seed_open(zara_task, zara),
    expert_eligibility:eligible_task(zara_task).

test(local_recall_freeze_exception_is_eligible,
     [setup(reset_freeze_tasks), cleanup(reset_freeze_tasks)]) :-
    seed_open(recall_task, local_recall),
    expert_eligibility:eligible_task(recall_task).

test(non_coding_auto_dig_remains_eligible,
     [setup(reset_freeze_tasks), cleanup(reset_freeze_tasks)]) :-
    seed_open(auto_dig_task, hourly_auto_dig),
    expert_eligibility:eligible_task(auto_dig_task).

:- end_tests(freeze_eligibility).
