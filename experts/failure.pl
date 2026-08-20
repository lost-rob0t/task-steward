:- module(expert_failure, [
    retryable_failure/1,
    deterministic_failure/1,
    failure_signature/2,
    retry_class/2
]).

:- use_module('../kb/evidence.pl').

transient_class(timeout).
transient_class(infrastructure).
transient_class(rate_limit).
transient_class(transient).

deterministic_class(build).
deterministic_class(test).
deterministic_class(lint).
deterministic_class(typecheck).
deterministic_class(packaging).
deterministic_class(policy).
deterministic_class(regression).

retryable_failure(Run) :-
    run_failure(Run, Class, _),
    transient_class(Class).

deterministic_failure(Run) :-
    run_failure(Run, Class, _),
    deterministic_class(Class).

retry_class(Run, retry) :-
    retryable_failure(Run), !.
retry_class(Run, stop) :-
    deterministic_failure(Run), !.
retry_class(Run, unknown) :-
    run_failure(Run, _, _).

% Stable across run identifiers: the signature is derived only from the
% normalized failure class and evidence detail. Callers should mirror
% structured/normalized detail rather than timestamps or transient run IDs.
failure_signature(Run, Signature) :-
    run_failure(Run, Class, Detail),
    term_string(failure(Class, Detail), Canonical, [quoted(true), numbervars(true)]),
    crypto_data_hash(Canonical, Hash, [algorithm(sha256), encoding(utf8)]),
    atom_string(Signature, Hash).
