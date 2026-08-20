:- module(expert_registry, [
    expert/1,
    expert_order/2
]).

expert(eligibility).
expert(dependencies).
expert(failure).
expert(regression).
expert(priority).
expert(skip_policy).
expert(scheduling).
expert(handoff).
expert(completion).

expert_order(eligibility, 10).
expert_order(dependencies, 20).
expert_order(failure, 30).
expert_order(regression, 40).
expert_order(priority, 50).
expert_order(skip_policy, 60).
expert_order(scheduling, 70).
expert_order(handoff, 80).
expert_order(completion, 90).
