:- module(kb_decisions, [decision_receipt/7]).

:- dynamic decision_receipt/7.

% decision_receipt(Id, Action, Subject, Generation, Owner, Reason, Evidence).
% These are mirrored durable facts. For task execution, Generation and Owner
% must still match the current fenced lease before the receipt is authoritative.
