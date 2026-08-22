:- module(kb_handoffs, []).

% Compatibility wrapper. Authoritative handoff state is generated from
% state/handoffs.yml by scripts/compile_state.py.
:- reexport('generated/handoffs.pl').
