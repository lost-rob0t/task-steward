% GENERATED FILE. DO NOT EDIT.
% Source: state/automations.yml
:- module(kb_generated_automations, [automation/1, automation_state/2, automation_title/2, automation_project/2, observed_by/1, observed_at/1, reconciliation_value/2, reconciliation_member/2]).

automation('6a54903dc26081918683fbdbc2c6c7cd').
automation_state('6a54903dc26081918683fbdbc2c6c7cd', active).
automation_title('6a54903dc26081918683fbdbc2c6c7cd', 'Task Steward').
automation_project('6a54903dc26081918683fbdbc2c6c7cd', task_stward_rage).

automation('6a7dce766d448191bca41ef6e0c9390e').
automation_state('6a7dce766d448191bca41ef6e0c9390e', paused).
automation_title('6a7dce766d448191bca41ef6e0c9390e', 'Book 1 Research Loop').
automation_project('6a7dce766d448191bca41ef6e0c9390e', chatgpt_books_book1).

automation('6a83847376348191b456e115c117d166').
automation_state('6a83847376348191b456e115c117d166', active).
automation_title('6a83847376348191b456e115c117d166', 'Hourly Auto-Dig').
automation_project('6a83847376348191b456e115c117d166', hourly_auto_dig).

automation('6a860d314d40819194128b7c7961fb99').
automation_state('6a860d314d40819194128b7c7961fb99', active).
automation_title('6a860d314d40819194128b7c7961fb99', 'StarIntel Discord Reports').
automation_project('6a860d314d40819194128b7c7961fb99', starintel_discord_reports).

automation('6a8649dc3f708191b51269995b51700a').
automation_state('6a8649dc3f708191b51269995b51700a', paused).
automation_title('6a8649dc3f708191b51269995b51700a', 'Prolog-RLM Subagent Loop').
automation_project('6a8649dc3f708191b51269995b51700a', prolog_rlm).

automation('6a864c35bce48191883144c38781b20e').
automation_state('6a864c35bce48191883144c38781b20e', paused).
automation_title('6a864c35bce48191883144c38781b20e', 'StarIntel Infra Deployment Gate').
automation_project('6a864c35bce48191883144c38781b20e', starintel_infra).

automation('6a87e25f61748191a30427f6020d14a3').
automation_state('6a87e25f61748191a30427f6020d14a3', paused).
automation_title('6a87e25f61748191a30427f6020d14a3', 'Prolog-RLM Integration Loop').

automation('6a87e26cb2208191a7f1c1ab222feae4').
automation_state('6a87e26cb2208191a7f1c1ab222feae4', paused).
automation_title('6a87e26cb2208191a7f1c1ab222feae4', 'AgentProlog Harness Loop A').

automation('6a87e2784aac8191b2ae9fc6d0bdf487').
automation_state('6a87e2784aac8191b2ae9fc6d0bdf487', paused).
automation_title('6a87e2784aac8191b2ae9fc6d0bdf487', 'AgentProlog Harness Loop B').

automation('6a892ef4c180819189cba1afee1a4504').
automation_state('6a892ef4c180819189cba1afee1a4504', active).
automation_title('6a892ef4c180819189cba1afee1a4504', 'Zara RAGE Worker').
automation_project('6a892ef4c180819189cba1afee1a4504', zara).

automation('6a8934a82ef881919ab153b6aec87c15').
automation_state('6a8934a82ef881919ab153b6aec87c15', active).
automation_title('6a8934a82ef881919ab153b6aec87c15', 'Local Recall RAGE Worker').
automation_project('6a8934a82ef881919ab153b6aec87c15', local_recall).

observed_by(task_steward).
observed_at('2026-08-22T07:58:00+00:00').
reconciliation_value([active_task_count], 5).
reconciliation_value([agentprolog_workers_enabled], false).
reconciliation_value([coding_freeze], active_with_explicit_exceptions).
reconciliation_member([coding_freeze_exception_workers], task_stward_rage).
reconciliation_member([coding_freeze_exception_workers], zara).
reconciliation_member([coding_freeze_exception_workers], local_recall).
reconciliation_value([coding_workers_active], 3).
reconciliation_value([infra_coding_worker_enabled], false).
reconciliation_value([infra_to_server_handoff], frozen_by_user).
reconciliation_value([prolog_rlm_workers_enabled], false).
reconciliation_value([unauthorized_coding_workers_active], 0).
