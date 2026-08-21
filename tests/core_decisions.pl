:- begin_tests(core_decisions).

:- use_module('../experts/priority.pl').
:- use_module('../experts/skip_policy.pl').
:- use_module('../experts/handoff.pl').
:- use_module('../experts/completion.pl').
:- use_module('../kb/tasks.pl').
:- use_module('../kb/evidence.pl').

clear_task(Task) :-
    retractall(kb_tasks:task(Task)),
    retractall(kb_tasks:task_project(Task, _)),
    retractall(kb_tasks:task_priority(Task, _)).

clear_skip_facts :-
    retractall(expert_skip_policy:mandatory_job(_)),
    retractall(expert_skip_policy:mandatory_test(_)),
    retractall(expert_skip_policy:job_irrelevant(_, _)),
    retractall(expert_skip_policy:test_irrelevant(_, _)).

clear_handoff_evidence :-
    retractall(kb_evidence:completion_gate(starintel_infra, automated_deployment_ready, _)),
    retractall(kb_evidence:blocking_failure(starintel_infra)).

clear_completion_evidence(Project, Gate) :-
    retractall(kb_evidence:completion_gate(Project, Gate, _)),
    retractall(kb_evidence:blocking_failure(Project)).

test(priority_combines_project_base_and_explicit_score,
     [setup(clear_task(priority_case)), cleanup(clear_task(priority_case))]) :-
    assertz(kb_tasks:task(priority_case)),
    assertz(kb_tasks:task_project(priority_case, prolog_rlm)),
    assertz(kb_tasks:task_priority(priority_case, 7)),
    expert_priority:priority_score(priority_case, 102).

test(nonmandatory_irrelevant_job_and_test_are_skippable,
     [setup(clear_skip_facts), cleanup(clear_skip_facts)]) :-
    assertz(expert_skip_policy:job_irrelevant(task_case, docs_job)),
    assertz(expert_skip_policy:test_irrelevant(task_case, docs_test)),
    expert_skip_policy:may_skip_job(task_case, docs_job),
    expert_skip_policy:may_skip_test(task_case, docs_test).

test(mandatory_job_and_test_are_never_skippable,
     [setup(clear_skip_facts), cleanup(clear_skip_facts)]) :-
    assertz(expert_skip_policy:job_irrelevant(task_case, merge_gate)),
    assertz(expert_skip_policy:test_irrelevant(task_case, production_test)),
    assertz(expert_skip_policy:mandatory_job(merge_gate)),
    assertz(expert_skip_policy:mandatory_test(production_test)),
    \+ expert_skip_policy:may_skip_job(task_case, merge_gate),
    \+ expert_skip_policy:may_skip_test(task_case, production_test).

test(infra_handoff_requires_satisfied_gate,
     [setup(clear_handoff_evidence), cleanup(clear_handoff_evidence), fail]) :-
    expert_handoff:handoff_ready(infra_to_server).

test(infra_handoff_fires_when_gate_is_satisfied,
     [setup(clear_handoff_evidence), cleanup(clear_handoff_evidence)]) :-
    assertz(kb_evidence:completion_gate(starintel_infra, automated_deployment_ready, satisfied)),
    expert_handoff:handoff_ready(infra_to_server).

test(blocking_failure_suppresses_satisfied_handoff,
     [setup(clear_handoff_evidence), cleanup(clear_handoff_evidence), fail]) :-
    assertz(kb_evidence:completion_gate(starintel_infra, automated_deployment_ready, satisfied)),
    assertz(kb_evidence:blocking_failure(starintel_infra)),
    expert_handoff:handoff_ready(infra_to_server).

test(project_completion_requires_satisfied_declared_gate,
     [setup(clear_completion_evidence(prolog_rlm, production_ready)),
      cleanup(clear_completion_evidence(prolog_rlm, production_ready)),
      fail]) :-
    expert_completion:project_complete(prolog_rlm).

test(project_completion_accepts_satisfied_declared_gate,
     [setup(clear_completion_evidence(prolog_rlm, production_ready)),
      cleanup(clear_completion_evidence(prolog_rlm, production_ready))]) :-
    assertz(kb_evidence:completion_gate(prolog_rlm, production_ready, satisfied)),
    expert_completion:project_complete(prolog_rlm).

test(blocking_failure_suppresses_satisfied_project_completion,
     [setup(clear_completion_evidence(prolog_rlm, production_ready)),
      cleanup(clear_completion_evidence(prolog_rlm, production_ready)),
      fail]) :-
    assertz(kb_evidence:completion_gate(prolog_rlm, production_ready, satisfied)),
    assertz(kb_evidence:blocking_failure(prolog_rlm)),
    expert_completion:project_complete(prolog_rlm).

test(project_without_completion_policy_cannot_complete,
     [fail]) :-
    expert_completion:project_complete(hourly_auto_dig).

:- end_tests(core_decisions).
