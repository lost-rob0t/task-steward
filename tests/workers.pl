:- begin_tests(worker_runtime).

:- use_module('../steward.pl').
:- use_module('../experts/workers.pl').
:- use_module('../kb/generated/workers.pl').

test(pure_enabled_keep_is_dispatchable) :-
    worker_dispatch_from(true, keep, dispatchable).

test(pure_disabled_worker_is_blocked) :-
    worker_dispatch_from(false, keep, blocked(worker_disabled)).

test(pure_project_pause_blocks_worker) :-
    worker_dispatch_from(true, pause, blocked(project_decision(pause))).

test(repository_agent_zero_worker_is_registered) :-
    worker(a0_starintel_server_1),
    worker_project(a0_starintel_server_1, starintel_server),
    worker_backend(a0_starintel_server_1, agent_zero_a2a),
    worker_enabled(a0_starintel_server_1).

test(repository_disabled_opencode_worker_is_not_dispatchable, [fail]) :-
    steward_worker_dispatchable(opencode_starintel_server_1, starintel_server, _).

test(repository_agent_zero_worker_follows_prolog_keep_decision) :-
    steward_worker_dispatchable(a0_starintel_server_1, starintel_server, protected_project).

test(current_generation_is_valid) :-
    runtime_generation_valid(19, 19).

test(stale_generation_is_invalid, [fail]) :-
    runtime_generation_valid(20, 19).

:- end_tests(worker_runtime).
