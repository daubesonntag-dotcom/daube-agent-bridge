#!/usr/bin/env python3
"""Offline real-SDK 1.2.2 constructor check. Never calls A2A transport."""
from __future__ import annotations

import hashlib
import json
import socket
import sys
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from daube_bridge.a2a_sdk_adapter import (  # noqa: E402
    create_sdk_client_config,
    create_sdk_request,
    plan_sdk_handoff,
)


def load(name: str):
    return json.loads((ROOT / 'examples' / 'collaboration' / name).read_text(encoding='utf-8'))


def verify() -> dict:
    if version('a2a-sdk') != '1.2.2':
        raise RuntimeError('This receipt requires a2a-sdk==1.2.2')
    card = load('agent-card.synthetic.json')
    request = load('request.synthetic.json')
    policy = load('policy.synthetic.json')
    # These tests must never establish an outbound connection, even accidentally.
    original_connect = socket.socket.connect
    network_calls = []

    def deny_network(self, *args, **kwargs):
        network_calls.append('denied')
        raise AssertionError('No network operation allowed during SDK contract test')

    socket.socket.connect = deny_network
    try:
        plan = plan_sdk_handoff(card, request, policy)
        typed = create_sdk_request(card, request, policy)
        config = create_sdk_client_config(card, request, policy)
        assert type(typed).__name__ == 'SendMessageRequest'
        assert typed.message.message_id == plan['message_id']
        assert len(typed.message.parts) == 1
        assert typed.message.parts[0].text == request['text']
        assert int(typed.message.role) == 1
        assert config.streaming is False and config.polling is False
        assert config.supported_protocol_bindings == ['HTTP+JSON']
        assert config.accepted_output_modes == ['text/plain']
        assert plan['external_action_authorized'] is False
        assert plan['sdk_transport_executed'] is False
        assert request['text'] not in json.dumps(plan)
        assert not network_calls

        card['defaultOutputModes'] = ['application/json']
        json_config = create_sdk_client_config(card, request, policy)
        assert json_config.accepted_output_modes == ['application/json']
    finally:
        socket.socket.connect = original_connect
    return {
        'state': 'SDK_V1_2_2_OFFLINE_CONTRACT_PASS',
        'sdk_version': '1.2.2',
        'request_type': 'SendMessageRequest',
        'message_id': plan['message_id'],
        'synthetic_text_sha256': hashlib.sha256(request['text'].encode()).hexdigest(),
        'client_streaming': False,
        'client_polling': False,
        'bindings_tested': ['HTTP+JSON'],
        'output_modes_tested': ['text/plain', 'application/json'],
        'sdk_transport_executed': False,
        'network_calls': len(network_calls),
        'external_action_authorized': False,
    }


if __name__ == '__main__':
    try:
        print(json.dumps(verify(), sort_keys=True))
    except (AssertionError, ValueError, RuntimeError, ImportError) as exc:
        print(json.dumps({'state': 'SDK_OFFLINE_CONTRACT_BLOCKED', 'error_class': type(exc).__name__}))
        sys.exit(2)
