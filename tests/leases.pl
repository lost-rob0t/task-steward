:- begin_tests(fenced_leases).

:- use_module('../kb/tasks.pl').
:- use_module('../kb/decisions.pl').
:- use_module('../experts/leases.pl').
:- use_module('../experts/receipts.pl').

reset_facts :-
    retractall(task(_)),
    retractall(task_state(_, _)),
    retractall(task_generation(_, _)),
    retractall(task_lease(_, _, _, _)),
    retractall(decision_receipt(_, _, _, _, _, _, _)).

seed_open_task(Task) :-
    assertz(task(Task)),
    assertz(task_state(Task, open)).

test(first_generation_is_one, [setup(reset_facts), cleanup(reset_facts)]) :-
    seed_open_task(issue_1),
    lease_candidate(issue_1, run_a, 1).

test(active_current_lease_blocks_second_owner, [setup(reset_facts), cleanup(reset_facts), fail]) :-
    seed_open_task(issue_1),
    assertz(task_generation(issue_1, 1)),
    assertz(task_lease(issue_1, 1, run_a, active)),
    lease_candidate(issue_1, run_b, _).

test(new_generation_fences_stale_owner, [setup(reset_facts), cleanup(reset_facts)]) :-
    seed_open_task(issue_1),
    assertz(task_lease(issue_1, 1, run_a, active)),
    assertz(task_generation(issue_1, 2)),
    assertz(task_lease(issue_1, 2, run_b, active)),
    stale_lease(issue_1, 1, run_a),
    \+ valid_lease(issue_1, 1, run_a),
    valid_lease(issue_1, 2, run_b).

test(current_generation_receipt_is_valid, [setup(reset_facts), cleanup(reset_facts)]) :-
    seed_open_task(issue_1),
    assertz(task_generation(issue_1, 3)),
    assertz(task_lease(issue_1, 3, run_c, active)),
    assertz(decision_receipt(r1, execute, issue_1, 3, run_c, selected_by_scheduler, evidence(ci_green))),
    valid_decision_receipt(r1),
    \+ stale_decision_receipt(r1).

test(stale_generation_receipt_is_rejected, [setup(reset_facts), cleanup(reset_facts)]) :-
    seed_open_task(issue_1),
    assertz(task_lease(issue_1, 1, run_a, active)),
    assertz(task_generation(issue_1, 2)),
    assertz(task_lease(issue_1, 2, run_b, active)),
    assertz(decision_receipt(r1, execute, issue_1, 1, run_a, selected_by_scheduler, evidence(old_head))),
    stale_decision_receipt(r1),
    \+ valid_decision_receipt(r1).

:- end_tests(fenced_leases).
