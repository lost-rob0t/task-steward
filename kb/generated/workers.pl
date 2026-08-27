% GENERATED FILE. DO NOT EDIT.
% Source: state/workers.yml
:- module(kb_generated_workers, [
    worker/1,
    worker_project/2,
    worker_backend/2,
    worker_enabled/1,
    worker_disabled/1,
    worker_capability/2,
    worker_config/3
]).

worker(a0_starintel_server_1).
worker_project(a0_starintel_server_1, starintel_server).
worker_backend(a0_starintel_server_1, agent_zero_a2a).
worker_enabled(a0_starintel_server_1).
worker_capability(a0_starintel_server_1, coding).
worker_capability(a0_starintel_server_1, rage).
worker_config(a0_starintel_server_1, base_url_env, 'STEWARD_A0_STARINTEL_URL').
worker_config(a0_starintel_server_1, project, 'StarIntelServer').
worker_config(a0_starintel_server_1, token_env, 'STEWARD_A0_STARINTEL_TOKEN').

worker(opencode_starintel_server_1).
worker_project(opencode_starintel_server_1, starintel_server).
worker_backend(opencode_starintel_server_1, opencode_run).
worker_disabled(opencode_starintel_server_1).
worker_capability(opencode_starintel_server_1, coding).
worker_capability(opencode_starintel_server_1, rage).
worker_config(opencode_starintel_server_1, agent, 'build').
worker_config(opencode_starintel_server_1, binary_env, 'STEWARD_OPENCODE_BIN').
worker_config(opencode_starintel_server_1, workdir_env, 'STEWARD_STARINTEL_WORKDIR').
