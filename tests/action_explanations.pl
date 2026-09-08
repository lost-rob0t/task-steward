:- begin_tests(action_explanations).

:- use_module('../steward.pl').
:- use_module('../kb/tasks.pl').
:- use_module('../kb/evidence.pl').
:- use_module('../experts/skip_policy.pl').

reset_explanation_facts :-
    retractall(kb_tasks:task(_)),
    retractall(kb_tasks:task_project(_, _)),
    retractall(kb_tasks:task_source(_, _)),
    retractall(kb_tasks:task_state(_, _)),
    retractall(kb_tasks:task_priority(_, _)),
    retractall(kb_tasks:task_dependency(_, _)),
    retractall(kb_tasks:task_generation(_, _)),
    retractall(kb_tasks:task_lease(_, _, _, _)),
    retractall(kb_evidence:regression(_, _, _)),
    retractall(kb_evidence:ci_status(_, _, _)),
    retractall(expert_skip_policy:mandatory_job(_)),
    retractall(expert_skip_policy:mandatory_test(_)),
    retractall(expert_skip_policy:job_irrelevant(_, _)),
    retractall(expert_skip_policy:test_irrelevant(_, _)).

seed_open_task(Task, Project) :-
    assertz(kb_tasks:task(Task)),
    assertz(kb_tasks:task_project(Task, Project)),
    assertz(kb_tasks:task_state(Task, open)).

test(selected_action_explains_priority_components,
     [setup(reset_explanation_facts), cleanup(reset_explanation_facts)]) :-
    seed_open_task(explain_selected, task_stward_rage),
    assertz(kb_tasks:task_priority(explain_selected, 3)),
    steward:steward_explain(
        execute(explain_selected),
        explanation(explain_selected, 13, Components)
    ),
    assertion(member(component(explicit, 3, explicit_task_priority), Components)),
    assertion(member(component(project_base, 10, project_base_priority(task_stward_rage)), Components)).

test(blocked_action_explains_unfinished_dependency,
     [setup(reset_explanation_facts), cleanup(reset_explanation_facts)]) :-
    seed_open_task(explain_blocked, task_stward_rage),
    assertz(kb_tasks:task(explain_dependency)),
    assertz(kb_tasks:task_state(explain_dependency, open)),
    assertz(kb_tasks:task_dependency(explain_blocked, explain_dependency)),
    steward:steward_explain(
        blocked(explain_blocked),
        explanation(explain_blocked, blocked, Reasons)
    ),
    assertion(member(dependency_not_completed(explain_dependency, open), Reasons)).

test(blocked_action_explains_active_fenced_lease,
     [setup(reset_explanation_facts), cleanup(reset_explanation_facts)]) :-
    seed_open_task(explain_leased, task_stward_rage),
    assertz(kb_tasks:task_generation(explain_leased, 4)),
    assertz(kb_tasks:task_lease(explain_leased, 4, worker_a, active)),
    steward:steward_explain(
        blocked(explain_leased),
        explanation(explain_leased, blocked, Reasons)
    ),
    assertion(member(active_lease(4, worker_a), Reasons)).

test(blocked_action_explains_blocking_regression,
     [setup(reset_explanation_facts), cleanup(reset_explanation_facts)]) :-
    seed_open_task(explain_regression, task_stward_rage),
    assertz(kb_evidence:regression(explain_regression, high, weakened_required_gate)),
    steward:steward_explain(
        blocked(explain_regression),
        explanation(explain_regression, blocked, Reasons)
    ),
    assertion(member(blocking_regression(high, weakened_required_gate), Reasons)).

test(blocked_action_explains_paused_project_policy,
     [setup(reset_explanation_facts), cleanup(reset_explanation_facts)]) :-
    seed_open_task(explain_paused, starintel_infra),
    steward:steward_explain(
        blocked(explain_paused),
        explanation(explain_paused, blocked, Reasons)
    ),
    assertion(member(project_policy(starintel_infra, project_status(paused_user)), Reasons)).

test(blocked_action_explains_hard_stop_policy,
     [setup(reset_explanation_facts), cleanup(reset_explanation_facts)]) :-
    seed_open_task(explain_hard_stop, local_recall),
    steward:steward_explain(
        blocked(explain_hard_stop),
        explanation(explain_hard_stop, blocked, Reasons)
    ),
    assertion(member(project_policy(local_recall, project_status(hard_paused_user)), Reasons)).

test(skip_job_explains_derived_policy_basis,
     [setup(reset_explanation_facts), cleanup(reset_explanation_facts)]) :-
    assertz(expert_skip_policy:job_irrelevant(explain_skip, docs_job)),
    steward:steward_explain(
        skip_job(explain_skip, docs_job),
        explanation(skip_job, job(explain_skip, docs_job),
                    skip_policy(job_irrelevant(explain_skip, docs_job), non_mandatory(docs_job)))
    ).

test(skip_test_explains_derived_policy_basis,
     [setup(reset_explanation_facts), cleanup(reset_explanation_facts)]) :-
    assertz(expert_skip_policy:test_irrelevant(explain_skip, docs_test)),
    steward:steward_explain(
        skip_test(explain_skip, docs_test),
        explanation(skip_test, test(explain_skip, docs_test),
                    skip_policy(test_irrelevant(explain_skip, docs_test), non_mandatory(docs_test)))
    ).

:- end_tests(action_explanations).
