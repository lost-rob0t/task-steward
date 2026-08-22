% GENERATED FILE. DO NOT EDIT.
% Source: state/deployment.yml
:- module(kb_generated_deployment, [deployment_declared_state/1, deployment_requirement/2, deployment_requirement_evidence/2]).

deployment_declared_state(building).

deployment_requirement(actions_wake_and_reconcile, satisfied).
deployment_requirement_evidence(actions_wake_and_reconcile, 'pr:#7').

deployment_requirement(decision_receipts, satisfied).
deployment_requirement_evidence(decision_receipts, 'pr:#17').
deployment_requirement_evidence(decision_receipts, 'pr:#6').

deployment_requirement(dependency_and_eligibility_reasoning, satisfied).
deployment_requirement_evidence(dependency_and_eligibility_reasoning, 'pr:#19').

deployment_requirement(durable_kb, satisfied).
deployment_requirement_evidence(durable_kb, 'pr:#22').

deployment_requirement(external_repo_write_isolation, satisfied).
deployment_requirement_evidence(external_repo_write_isolation, 'pr:#5').

deployment_requirement(failure_detection_and_retry_classification, satisfied).
deployment_requirement_evidence(failure_detection_and_retry_classification, 'pr:#8').

deployment_requirement(fenced_leases, satisfied).
deployment_requirement_evidence(fenced_leases, 'pr:#4').

deployment_requirement(green_required_ci, pending).
deployment_requirement_evidence(green_required_ci, 'requires:exact-head-ci-after-deployment-gate-change').

deployment_requirement(job_and_test_skip_reasoning, satisfied).
deployment_requirement_evidence(job_and_test_skip_reasoning, 'pr:#14').
deployment_requirement_evidence(job_and_test_skip_reasoning, 'pr:#17').

deployment_requirement(no_p0_p1_deployment_blockers, pending).
deployment_requirement_evidence(no_p0_p1_deployment_blockers, 'requires:post-change-backlog-reconciliation').

deployment_requirement(non_skippable_required_gates, satisfied).
deployment_requirement_evidence(non_skippable_required_gates, 'pr:#14').

deployment_requirement(priority_scoring, satisfied).
deployment_requirement_evidence(priority_scoring, 'pr:#14').

deployment_requirement(recursive_wake_protection, satisfied).
deployment_requirement_evidence(recursive_wake_protection, 'pr:#5').
deployment_requirement_evidence(recursive_wake_protection, 'pr:#7').

deployment_requirement(regression_detection, satisfied).
deployment_requirement_evidence(regression_detection, 'pr:#9').

deployment_requirement(scenario_regression_tests, satisfied).
deployment_requirement_evidence(scenario_regression_tests, 'pr:#12').
deployment_requirement_evidence(scenario_regression_tests, 'pr:#14').
deployment_requirement_evidence(scenario_regression_tests, 'pr:#15').

deployment_requirement(serial_prolog_moe, satisfied).
deployment_requirement_evidence(serial_prolog_moe, 'pr:#10').

deployment_requirement(structured_handoffs, satisfied).
deployment_requirement_evidence(structured_handoffs, 'pr:#18').

deployment_requirement(unified_steward_interface, satisfied).
deployment_requirement_evidence(unified_steward_interface, 'pr:#10').
deployment_requirement_evidence(unified_steward_interface, 'pr:#17').

deployment_requirement(validated_inline_prolog, satisfied).
deployment_requirement_evidence(validated_inline_prolog, 'pr:#3').

deployment_requirement(yaml_state, satisfied).
deployment_requirement_evidence(yaml_state, 'pr:#2').
deployment_requirement_evidence(yaml_state, 'pr:#22').

deployment_requirement(yaml_to_prolog_compiler, satisfied).
deployment_requirement_evidence(yaml_to_prolog_compiler, 'pr:#18').
deployment_requirement_evidence(yaml_to_prolog_compiler, 'pr:#19').
deployment_requirement_evidence(yaml_to_prolog_compiler, 'pr:#2').
deployment_requirement_evidence(yaml_to_prolog_compiler, 'pr:#20').
deployment_requirement_evidence(yaml_to_prolog_compiler, 'pr:#22').
