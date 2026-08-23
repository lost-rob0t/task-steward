% GENERATED FILE. DO NOT EDIT.
% Source: state/managed_github.yml
:- module(kb_generated_managed_github, [managed_observed_by/1, managed_observed_at/1, github_snapshot/4, github_work/2, github_work_kind/3, github_work_state/3, github_work_severity/3, github_work_readiness/3, github_work_ci/3, github_work_review/3, github_work_head_sha/3, github_work_updated_at/3, github_work_source/3]).

managed_observed_by(task_steward_github).
managed_observed_at('2026-08-23T20:34:00+00:00').

github_snapshot(chatgpt_books_book1, 'lost-rob0t/chatgpt-books', unavailable, '2026-08-23T20:34:00+00:00').
github_snapshot(hourly_auto_dig, 'lost-rob0t/starintel-gpt-auto-dig', unavailable, '2026-08-23T20:34:00+00:00').
github_snapshot(local_recall, 'lost-rob0t/local-recall', unavailable, '2026-08-23T20:34:00+00:00').
github_snapshot(prolog_rlm, 'lost-rob0t/prolog-rlm', unavailable, '2026-08-23T20:34:00+00:00').
github_snapshot(starintel_discord_reports, 'lost-rob0t/starintel-discord-reporting', unavailable, '2026-08-23T20:34:00+00:00').
github_snapshot(starintel_infra, 'starintel-labs/starintel-infra', unavailable, '2026-08-23T20:34:00+00:00').
github_snapshot(starintel_server, 'lost-rob0t/starintel-server', partial, '2026-08-23T20:34:00+00:00').
github_work(starintel_server, pr_105).
github_work_kind(starintel_server, pr_105, pr).
github_work_state(starintel_server, pr_105, open).
github_work_severity(starintel_server, pr_105, normal).
github_work_readiness(starintel_server, pr_105, ready).
github_work_ci(starintel_server, pr_105, failure).
github_work_review(starintel_server, pr_105, unknown).
github_work_head_sha(starintel_server, pr_105, '055c8bfdb5f291c764decd676c2163911e851021').
github_work_updated_at(starintel_server, pr_105, '2026-08-23T03:20:18+00:00').
github_work_source(starintel_server, pr_105, 'github-pr:lost-rob0t/starintel-server#105').

github_snapshot(zara, 'lost-rob0t/zara', partial, '2026-08-23T20:34:00+00:00').
github_work(zara, pr_188).
github_work_kind(zara, pr_188, pr).
github_work_state(zara, pr_188, open).
github_work_severity(zara, pr_188, normal).
github_work_readiness(zara, pr_188, ready).
github_work_ci(zara, pr_188, failure).
github_work_review(zara, pr_188, unknown).
github_work_head_sha(zara, pr_188, '8272d9499104581bf5eae642b252c38f284865bb').
github_work_updated_at(zara, pr_188, '2026-08-23T20:12:31+00:00').
github_work_source(zara, pr_188, 'github-pr:lost-rob0t/zara#188').
