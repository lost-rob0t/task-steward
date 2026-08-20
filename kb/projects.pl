:- module(kb_projects, [
    project/1,
    project_repo/2,
    project_status/2,
    project_mode/2,
    base_priority/2,
    protected_project/1,
    completion_policy/2
]).

project(hourly_auto_dig).
project(starintel_discord_reports).
project(prolog_rlm).
project(starintel_infra).
project(starintel_server).
project(chatgpt_books_book1).
project(task_stward_rage).

project_repo(hourly_auto_dig, 'lost-rob0t/starintel-gpt-auto-dig').
project_repo(starintel_discord_reports, 'lost-rob0t/starintel-discord-reporting').
project_repo(prolog_rlm, 'lost-rob0t/prolog-rlm').
project_repo(starintel_infra, 'starintel-labs/starintel-infra').
project_repo(starintel_server, 'lost-rob0t/starintel-server').
project_repo(chatgpt_books_book1, 'lost-rob0t/chatgpt-books').
project_repo(task_stward_rage, 'lost-rob0t/task-stward-rage').

project_status(hourly_auto_dig, active).
project_status(starintel_discord_reports, active).
project_status(prolog_rlm, active).
project_status(starintel_infra, active).
project_status(starintel_server, waiting_handoff).
project_status(chatgpt_books_book1, paused).
project_status(task_stward_rage, active).

project_mode(hourly_auto_dig, permanent).
project_mode(starintel_discord_reports, permanent).
project_mode(prolog_rlm, rage).
project_mode(starintel_infra, rage).
project_mode(starintel_server, rage).
project_mode(chatgpt_books_book1, research).
project_mode(task_stward_rage, self_rage_when_idle).

base_priority(hourly_auto_dig, 100).
base_priority(starintel_discord_reports, 100).
base_priority(prolog_rlm, 95).
base_priority(starintel_infra, 90).
base_priority(starintel_server, 90).
base_priority(chatgpt_books_book1, 60).
base_priority(task_stward_rage, 10).

protected_project(hourly_auto_dig).
protected_project(starintel_discord_reports).
protected_project(prolog_rlm).

completion_policy(prolog_rlm, production_ready).
completion_policy(starintel_infra, automated_deployment_ready).
completion_policy(starintel_server, production_ready).
