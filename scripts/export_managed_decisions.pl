:- use_module('../steward.pl').
:- use_module('../kb/generated/projects.pl').
:- use_module('../kb/generated/managed_github.pl').
:- use_module(library(http/json)).

worker_entry(Project-_{project:Project, decision:Decision, reason:ReasonText}) :-
    kb_generated_projects:project(Project),
    Project \= task_stward_rage,
    steward:steward_worker_decision(Project, Decision, Reason),
    term_string(Reason, ReasonText, [quoted(true)]).

next_external_dict(Dict) :-
    steward:steward_next_external(Project, Ref),
    steward:steward_explain(
        external(Project, Ref),
        explanation(external, Project, Ref, Score, Source, Snapshot)
    ),
    Dict = _{
        project:Project,
        ref:Ref,
        score:Score,
        source:Source,
        snapshot:Snapshot
    },
    !.
next_external_dict(null).

main :-
    findall(Pair, worker_entry(Pair), RawWorkers),
    keysort(RawWorkers, SortedWorkers),
    pairs_values(SortedWorkers, Workers),
    next_external_dict(NextExternal),
    kb_generated_managed_github:managed_observed_by(ObservedBy),
    kb_generated_managed_github:managed_observed_at(ObservedAt),
    Document = _{
        version:1,
        authority:prolog,
        evidence_observed_by:ObservedBy,
        evidence_observed_at:ObservedAt,
        workers:Workers,
        next_external:NextExternal
    },
    json_write_dict(current_output, Document, [width(0)]),
    nl.
