:- begin_tests(expert_pipeline).

:- use_module('../steward.pl').

expected_order([
    5-leases,
    10-eligibility,
    20-dependencies,
    30-failure,
    40-regression,
    50-priority,
    60-skip_policy,
    70-scheduling,
    80-handoff,
    90-completion,
    91-prolog_rlm_readiness,
    95-receipts
]).

test(full_pipeline_is_deterministic_and_complete) :-
    steward_evaluate(Executions),
    findall(Order-Expert,
        member(expert_execution(Expert, _, Order, _), Executions),
        Actual),
    expected_order(Actual).

test(custom_expert_executes_at_declared_stage) :-
    steward_evaluate_stage(completion, Executions),
    member(expert_execution(prolog_rlm_readiness, completion, 91, _), Executions).

test(stage_filter_excludes_other_stages) :-
    steward_evaluate_stage(scheduling, Executions),
    forall(member(expert_execution(_, Stage, _, _), Executions), Stage == scheduling).

:- end_tests(expert_pipeline).
