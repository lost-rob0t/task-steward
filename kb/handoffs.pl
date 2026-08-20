:- module(kb_handoffs, [
    handoff/3,
    handoff_status/2,
    handoff_gate/2
]).

handoff(infra_to_server, starintel_infra, starintel_server).
handoff_status(infra_to_server, armed).
handoff_gate(infra_to_server, automated_deployment_ready).
