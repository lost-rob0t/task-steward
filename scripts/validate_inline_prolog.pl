:- initialization(main, main).

main(Argv) :-
    catch(run(Argv), Error, fail_with(Error)).

run([Path|AllowedAtoms]) :-
    !,
    maplist(parse_indicator, AllowedAtoms, Allowed),
    setup_call_cleanup(
        open(Path, read, Stream, [encoding(utf8)]),
        read_terms(Stream, Terms),
        close(Stream)
    ),
    defined_predicates(Terms, Defined),
    maplist(validate_term(Defined, Allowed), Terms).
run(_) :-
    throw(error(domain_error(arguments, expected_path_and_allowlist), _)).

fail_with(Error) :-
    print_message(error, Error),
    halt(2).

parse_indicator(Atom, Name/Arity) :-
    atomic_list_concat([NameAtom, ArityAtom], '/', Atom),
    atom_string(NameAtom, NameString),
    valid_name(NameString),
    atom_number(ArityAtom, Arity),
    integer(Arity),
    Arity >= 0,
    atom_string(Name, NameString),
    !.
parse_indicator(Atom, _) :-
    throw(error(domain_error(predicate_indicator, Atom), _)).

valid_name(String) :-
    string_codes(String, [First|Rest]),
    code_type(First, lower),
    maplist(identifier_code, Rest).

identifier_code(Code) :-
    code_type(Code, alnum),
    !.
identifier_code(0'_).

read_terms(Stream, Terms) :-
    read_term(Stream, Term, [syntax_errors(error)]),
    (   Term == end_of_file
    ->  Terms = []
    ;   Terms = [Term|Rest],
        read_terms(Stream, Rest)
    ).

defined_predicates(Terms, Defined) :-
    findall(Indicator, (member(Term, Terms), term_head(Term, Head), head_indicator(Head, Indicator)), Raw),
    sort(Raw, Defined).

term_head((Head :- _), Head) :- !.
term_head((:- _), _) :-
    throw(error(permission_error(load, directive, inline_prolog), _)).
term_head((?- _), _) :-
    throw(error(permission_error(execute, query, inline_prolog), _)).
term_head(Term, Term).

head_indicator(Head, Name/Arity) :-
    nonvar(Head),
    callable(Head),
    \+ module_qualified(Head),
    functor(Head, Name, Arity),
    atom(Name),
    \+ reserved_control(Name/Arity),
    !.
head_indicator(Head, _) :-
    throw(error(domain_error(rule_head, Head), _)).

validate_term(Defined, Allowed, (Head :- Body)) :-
    !,
    head_indicator(Head, _),
    validate_goal(Defined, Allowed, Body).
validate_term(_, _, (:- Directive)) :-
    !,
    throw(error(permission_error(load, directive, Directive), _)).
validate_term(_, _, (?- Query)) :-
    !,
    throw(error(permission_error(execute, query, Query), _)).
validate_term(_, _, Fact) :-
    head_indicator(Fact, _).

validate_goal(Defined, Allowed, (A, B)) :-
    !,
    validate_goal(Defined, Allowed, A),
    validate_goal(Defined, Allowed, B).
validate_goal(Defined, Allowed, (A ; B)) :-
    !,
    validate_goal(Defined, Allowed, A),
    validate_goal(Defined, Allowed, B).
validate_goal(Defined, Allowed, (A -> B)) :-
    !,
    validate_goal(Defined, Allowed, A),
    validate_goal(Defined, Allowed, B).
validate_goal(Defined, Allowed, \+ Goal) :-
    !,
    validate_goal(Defined, Allowed, Goal).
validate_goal(_, _, Goal) :-
    var(Goal),
    !,
    throw(error(permission_error(call, variable_goal, Goal), _)).
validate_goal(_, _, Goal) :-
    module_qualified(Goal),
    !,
    throw(error(permission_error(call, module_qualified_goal, Goal), _)).
validate_goal(Defined, Allowed, Goal) :-
    callable(Goal),
    functor(Goal, Name, Arity),
    Indicator = Name/Arity,
    (   memberchk(Indicator, Defined)
    ;   memberchk(Indicator, Allowed)
    ;   pure_builtin(Indicator)
    ),
    !.
validate_goal(_, _, Goal) :-
    callable(Goal),
    functor(Goal, Name, Arity),
    throw(error(permission_error(call, non_allowlisted_predicate, Name/Arity), _)).
validate_goal(_, _, Goal) :-
    throw(error(type_error(callable, Goal), _)).

module_qualified(Term) :-
    nonvar(Term),
    Term = (_:_).

reserved_control((:-)/1).
reserved_control((?-)/1).
reserved_control((,)/2).
reserved_control((;)/2).
reserved_control((->)/2).
reserved_control((\+)/1).

pure_builtin(true/0).
pure_builtin(fail/0).
pure_builtin((=)/2).
pure_builtin((\=)/2).
pure_builtin((==)/2).
pure_builtin((\==)/2).
pure_builtin((@<)/2).
pure_builtin((@=<)/2).
pure_builtin((@>)/2).
pure_builtin((@>=)/2).
pure_builtin((is)/2).
pure_builtin((=:=)/2).
pure_builtin((=\=)/2).
pure_builtin((<)/2).
pure_builtin((=<)/2).
pure_builtin((>)/2).
pure_builtin((>=)/2).
