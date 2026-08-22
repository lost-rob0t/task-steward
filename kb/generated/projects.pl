% GENERATED FILE. DO NOT EDIT.
% Source: state/projects.yml
:- module(kb_generated_projects, [
    project/1,
    project_repo/2,
    project_status/2,
    project_mode/2,
    base_priority/2,
    protected_project/1,
    completion_policy/2
]).

project(hourly_auto_dig).
project_repo(hourly_auto_dig, 'lost-rob0t/starintel-gpt-auto-dig').
project_status(hourly_auto_dig, active).
project_mode(hourly_auto_dig, permanent_non_coding).
base_priority(hourly_auto_dig, 100).
protected_project(hourly_auto_dig).

project(starintel_discord_reports).
project_repo(starintel_discord_reports, 'lost-rob0t/starintel-discord-reporting').
project_status(starintel_discord_reports, active).
project_mode(starintel_discord_reports, permanent_non_coding).
base_priority(starintel_discord_reports, 100).
protected_project(starintel_discord_reports).

project(zara).
project_repo(zara, 'lost-rob0t/zara').
project_status(zara, active_freeze_exception).
project_mode(zara, rage).
base_priority(zara, 95).
protected_project(zara).

project(local_recall).
project_repo(local_recall, 'lost-rob0t/local-recall').
project_status(local_recall, active_freeze_exception).
project_mode(local_recall, rage).
base_priority(local_recall, 95).
protected_project(local_recall).

project(prolog_rlm).
project_repo(prolog_rlm, 'lost-rob0t/prolog-rlm').
project_status(prolog_rlm, frozen_user_stop).
project_mode(prolog_rlm, paused).
base_priority(prolog_rlm, 95).
protected_project(prolog_rlm).
completion_policy(prolog_rlm, production_ready).

project(starintel_infra).
project_repo(starintel_infra, 'starintel-labs/starintel-infra').
project_status(starintel_infra, frozen_user).
project_mode(starintel_infra, paused).
base_priority(starintel_infra, 90).
completion_policy(starintel_infra, automated_deployment_ready).

project(starintel_server).
project_repo(starintel_server, 'lost-rob0t/starintel-server').
project_status(starintel_server, frozen_waiting_handoff).
project_mode(starintel_server, paused).
base_priority(starintel_server, 90).
completion_policy(starintel_server, production_ready).

project(chatgpt_books_book1).
project_repo(chatgpt_books_book1, 'lost-rob0t/chatgpt-books').
project_status(chatgpt_books_book1, paused).
project_mode(chatgpt_books_book1, research).
base_priority(chatgpt_books_book1, 60).

project(task_stward_rage).
project_repo(task_stward_rage, 'lost-rob0t/task-stward-rage').
project_status(task_stward_rage, active_freeze_exception).
project_mode(task_stward_rage, self_rage_building_experts).
base_priority(task_stward_rage, 10).
