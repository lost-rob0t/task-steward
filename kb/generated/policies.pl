% GENERATED FILE. DO NOT EDIT.
% Source: state/policies.yml
:- module(kb_generated_policies, [
    policy_version/1,
    policy_value/2,
    policy_member/2
]).

policy_version(3).
policy_value([backlog, blocked_work_fallback], backlog_hygiene).
policy_value([backlog, complete_enumeration_required_before_no_work_claim], true).
policy_value([backlog, include_failed_or_pending_ci], true).
policy_value([backlog, include_open_issues], true).
policy_value([backlog, include_open_prs], true).
policy_value([backlog, include_unfinished_transactions], true).
policy_value([backlog, partial_sweep_must_not_be_reported_as_complete], true).
policy_value([backlog, prefer_valid_existing_backlog], true).
policy_value([context, current_prompt_is_not_complete_context], true).
policy_value([context, personal_context_required_before_action], true).
policy_value([context, resolve_ambiguity_from_memory_and_repository_state], true).
policy_member([expert_system_deployment, requires], yaml_state).
policy_member([expert_system_deployment, requires], yaml_to_prolog_compiler).
policy_member([expert_system_deployment, requires], validated_inline_prolog).
policy_member([expert_system_deployment, requires], durable_kb).
policy_member([expert_system_deployment, requires], serial_prolog_moe).
policy_member([expert_system_deployment, requires], unified_steward_interface).
policy_member([expert_system_deployment, requires], priority_scoring).
policy_member([expert_system_deployment, requires], dependency_and_eligibility_reasoning).
policy_member([expert_system_deployment, requires], failure_detection_and_retry_classification).
policy_member([expert_system_deployment, requires], regression_detection).
policy_member([expert_system_deployment, requires], job_and_test_skip_reasoning).
policy_member([expert_system_deployment, requires], non_skippable_required_gates).
policy_member([expert_system_deployment, requires], fenced_leases).
policy_member([expert_system_deployment, requires], structured_handoffs).
policy_member([expert_system_deployment, requires], decision_receipts).
policy_member([expert_system_deployment, requires], actions_wake_and_reconcile).
policy_member([expert_system_deployment, requires], recursive_wake_protection).
policy_member([expert_system_deployment, requires], scenario_regression_tests).
policy_member([expert_system_deployment, requires], external_repo_write_isolation).
policy_member([expert_system_deployment, requires], green_required_ci).
policy_member([expert_system_deployment, requires], no_p0_p1_deployment_blockers).
policy_value([expert_system_deployment, state], building).
policy_value([project_work_order, hourly_auto_dig, free_range_only_when_primary_queue_and_unrelated_backlog_empty], true).
policy_value([project_work_order, hourly_auto_dig, open_requests_before_unrelated_backlog], true).
policy_value([project_work_order, hourly_auto_dig, primary_queue], investigation_target).
policy_value([project_work_order, hourly_auto_dig, request_associated_pr_repair_counts_as_request_work], true).
policy_value([project_work_order, hourly_auto_dig, unrelated_backlog_only_when_primary_queue_empty], true).
policy_member([protected_projects], hourly_auto_dig).
policy_member([protected_projects], starintel_discord_reports).
policy_member([protected_projects], task_stward_rage).
policy_member([protected_projects], zara).
policy_member([protected_projects], local_recall).
policy_member([reporting_house_style, applies_to], auto_dig).
policy_member([reporting_house_style, applies_to], research_reporting).
policy_member([reporting_house_style, applies_to], discord_reporting).
policy_value([reporting_house_style, evidence_discipline_required], true).
policy_member([reporting_house_style, never_invent], crimes).
policy_member([reporting_house_style, never_invent], motives).
policy_member([reporting_house_style, never_invent], quotes).
policy_member([reporting_house_style, never_invent], certainty).
policy_member([reporting_house_style, tone], clipped).
policy_member([reporting_house_style, tone], cynical).
policy_member([reporting_house_style, tone], punchy).
policy_member([reporting_house_style, tone], minimal_ai_slop).
policy_value([scheduling, authority], prolog).
policy_value([scheduling, coding_freeze_overrides_scheduler], true).
policy_value([scheduling, expert_mode], serial).
policy_value([scheduling, explicit_freeze_exceptions_override_general_freeze], true).
policy_value([scheduling, llm_may_directly_approve_handoff], false).
policy_value([scheduling, llm_may_directly_schedule], false).
policy_value([scheduling, llm_may_directly_score_priority], false).
policy_value([scheduling, llm_may_directly_skip_required_gate], false).
policy_value([scope, exclusive_consumer], task_steward).
policy_value([scope, external_repo_mutation], forbidden).
policy_value([scope, issue_source_of_truth], owning_repository).
policy_value([scope, managed_project_code_in_this_repo], forbidden).
policy_value([self_rage, changes_require_issue], true).
policy_value([self_rage, changes_require_regression_validation], true).
policy_value([self_rage, deployment_gate], expert_system_fully_deployed).
policy_value([self_rage, enabled], true).
policy_value([self_rage, post_deployment_mode], fallback_when_no_schedulable_work).
policy_value([self_rage, pre_deployment_mode], mandatory_after_task_reconciliation).
policy_value([self_rage, pre_deployment_wait_for_empty_queue], false).
policy_value([skip_policy, required_merge_gates_skippable], false).
policy_value([skip_policy, skipped_jobs_require_reason], true).
policy_value([skip_policy, skipped_tests_require_reason], true).
policy_value([user_freeze, active], true).
policy_member([user_freeze, allowed_non_coding_modes], task_reconciliation).
policy_member([user_freeze, allowed_non_coding_modes], reminders).
policy_member([user_freeze, allowed_non_coding_modes], research_when_separately_authorized).
policy_member([user_freeze, allowed_non_coding_modes], reporting).
policy_member([user_freeze, allowed_non_coding_modes], non_coding_observation).
policy_value([user_freeze, autonomous_resume_allowed], false).
policy_value([user_freeze, coding_implementation_loops_allowed], exceptions_only).
policy_value([user_freeze, explicit_coding_exceptions, local_recall, automation_id], '6a8934a82ef881919ab153b6aec87c15').
policy_value([user_freeze, explicit_coding_exceptions, local_recall, may_pause_without_new_user_instruction], false).
policy_value([user_freeze, explicit_coding_exceptions, local_recall, protected_during_freeze], true).
policy_value([user_freeze, explicit_coding_exceptions, local_recall, repo], 'lost-rob0t/local-recall').
policy_value([user_freeze, explicit_coding_exceptions, task_stward_rage, automation_id], '6a54903dc26081918683fbdbc2c6c7cd').
policy_value([user_freeze, explicit_coding_exceptions, task_stward_rage, may_pause_without_new_user_instruction], false).
policy_value([user_freeze, explicit_coding_exceptions, task_stward_rage, protected_during_freeze], true).
policy_value([user_freeze, explicit_coding_exceptions, task_stward_rage, repo], 'lost-rob0t/task-stward-rage').
policy_value([user_freeze, explicit_coding_exceptions, zara, automation_id], '6a892ef4c180819189cba1afee1a4504').
policy_value([user_freeze, explicit_coding_exceptions, zara, may_pause_without_new_user_instruction], false).
policy_value([user_freeze, explicit_coding_exceptions, zara, protected_during_freeze], true).
policy_value([user_freeze, explicit_coding_exceptions, zara, repo], 'lost-rob0t/zara').
policy_value([user_freeze, hard_stops, agentprolog_deepseek_integration, audit_allowed], false).
policy_value([user_freeze, hard_stops, agentprolog_deepseek_integration, automation_allowed], false).
policy_value([user_freeze, hard_stops, agentprolog_deepseek_integration, implementation_allowed], false).
policy_value([user_freeze, hard_stops, agentprolog_deepseek_integration, research_allowed], false).
policy_value([user_freeze, hard_stops, agentprolog_deepseek_integration, resume_requires], explicit_user_authorization).
policy_value([user_freeze, hard_stops, prolog_rlm, audit_allowed], false).
policy_value([user_freeze, hard_stops, prolog_rlm, automation_allowed], false).
policy_value([user_freeze, hard_stops, prolog_rlm, implementation_allowed], false).
policy_value([user_freeze, hard_stops, prolog_rlm, research_allowed], false).
policy_value([user_freeze, hard_stops, prolog_rlm, resume_requires], explicit_user_authorization).
policy_value([user_freeze, infra_to_server_handoff_allowed], false).
policy_value([user_freeze, resume_requires], explicit_user_authorization).
policy_value([user_freeze, set_at], '2026-08-21').
policy_value([user_freeze, steward_self_coding_allowed], true).
policy_value([wake, dual_wake_and_state_markers], forbidden).
policy_value([wake, empty_commit_allowed], true).
policy_value([wake, manual_dispatch_may_evaluate], true).
policy_value([wake, meaning], reevaluate_only).
policy_value([wake, ordinary_pushes_are_validation_only], true).
policy_value([wake, pull_requests_are_validation_only], true).
policy_value([wake, self_generated_state_commits_must_not_recurse], true).
policy_value([wake, state_commit_marker], '[steward-state]').
policy_value([wake, wake_commit_marker], '[steward-wake]').
