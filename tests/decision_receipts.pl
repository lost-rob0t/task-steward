:- begin_tests(decision_receipts).

:- use_module('../kb/decisions.pl').
:- use_module('../kb/evidence.pl').
:- use_module('../experts/skip_policy.pl').
:- use_module('../experts/receipts.pl').

reset_receipt_facts :-
    retractall(decision_receipt(_, _, _, _, _, _, _)),
    retractall(completion_gate(_, _, _)),
    retractall(blocking_failure(_)),
    retractall(expert_skip_policy:mandatory_job(_)),
    retractall(expert_skip_policy:mandatory_test(_)),
    retractall(expert_skip_policy:job_irrelevant(_, _)),
    retractall(expert_skip_policy:test_irrelevant(_, _)).

test(arbitrary_system_action_is_not_authoritative,
     [setup(reset_receipt_facts), cleanup(reset_receipt_facts), fail]) :-
    assertz(decision_receipt(r_bad, invent_authority, task_1, 0, system, because_i_said_so, evidence(none))),
    valid_decision_receipt(r_bad).

test(skip_job_requires_derived_irrelevance,
     [setup(reset_receipt_facts), cleanup(reset_receipt_facts)]) :-
    assertz(expert_skip_policy:job_irrelevant(task_1, docs)),
    assertz(decision_receipt(r_skip, skip_job, job(task_1, docs), 0, system,
                             derived_irrelevant, evidence(scope_only))),
    valid_decision_receipt(r_skip),
    decision_receipt_explanation(
        r_skip,
        explanation(skip_job, job(task_1, docs), derived_irrelevant,
                    evidence(scope_only), skip_policy(job, task_1, docs))
    ).

test(mandatory_job_cannot_be_skipped,
     [setup(reset_receipt_facts), cleanup(reset_receipt_facts), fail]) :-
    assertz(expert_skip_policy:job_irrelevant(task_1, required_ci)),
    assertz(expert_skip_policy:mandatory_job(required_ci)),
    assertz(decision_receipt(r_skip, skip_job, job(task_1, required_ci), 0, system,
                             derived_irrelevant, evidence(scope_only))),
    valid_decision_receipt(r_skip).

test(skip_test_requires_derived_irrelevance,
     [setup(reset_receipt_facts), cleanup(reset_receipt_facts)]) :-
    assertz(expert_skip_policy:test_irrelevant(task_1, browser_test)),
    assertz(decision_receipt(r_skip_test, skip_test, test(task_1, browser_test), 0, system,
                             derived_irrelevant, evidence(no_ui_change))),
    valid_decision_receipt(r_skip_test).

test(handoff_receipt_is_invalid_while_target_is_frozen,
     [setup(reset_receipt_facts), cleanup(reset_receipt_facts), fail]) :-
    assertz(completion_gate(starintel_infra, automated_deployment_ready, satisfied)),
    assertz(decision_receipt(r_handoff, handoff,
                             handoff(infra_to_server, starintel_infra, starintel_server),
                             0, system, gate_satisfied, evidence(ci_green))),
    valid_decision_receipt(r_handoff).

test(handoff_receipt_without_gate_is_invalid,
     [setup(reset_receipt_facts), cleanup(reset_receipt_facts), fail]) :-
    assertz(decision_receipt(r_handoff, handoff,
                             handoff(infra_to_server, starintel_infra, starintel_server),
                             0, system, gate_satisfied, evidence(ci_green))),
    valid_decision_receipt(r_handoff).

test(completion_receipt_requires_completion_gate,
     [setup(reset_receipt_facts), cleanup(reset_receipt_facts)]) :-
    assertz(completion_gate(starintel_infra, automated_deployment_ready, satisfied)),
    assertz(decision_receipt(r_complete, complete, starintel_infra, 0, system,
                             completion_gate_satisfied, evidence(ci_green))),
    valid_decision_receipt(r_complete).

:- end_tests(decision_receipts).
