import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from dataclasses import replace
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ti_messenger_mcp import Client, Config, ACTOR_BY_ACCESS_CLIENT_ID
from outbox import Outbox, Message
from messenger_adapter import MessengerTransport, adapt_send_result

ENDPOINT = 'https://office-origin.daubesonntag.com/api/agent-chat/rooms/council/messages'
MID = '75e7af2c-55f0-4d0e-8932-8f02ebbd73d1'
PAYLOAD = {'text': 'Offline fixture', 'kind': 'text'}
MESSAGE = Message('operation_123456', MID, 'agent:ti', 'council',
                  json.dumps(PAYLOAD, sort_keys=True, separators=(',', ':')), 3)


def receipt(actor='agent:ti'):
    return {'id': 'server-uuid-fixture', 'from': actor, 'clientMessageId': MID,
            'room': 'council', 'tenantId': 'daube', **PAYLOAD}


class Response:
    status = 201
    def __init__(self, data):
        self.data = io.BytesIO(json.dumps(data).encode())
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return None
    def read(self, size):
        return self.data.read(size)


class Opener:
    def __init__(self, data):
        self.data = data
        self.calls = []
    def open(self, request, timeout):
        self.calls.append(request)
        if isinstance(self.data, Exception):
            raise self.data
        return Response(self.data)


def client(opener, actor='agent:ti', client_id=None):
    if client_id is None:
        client_id = next(key for key, value in ACTOR_BY_ACCESS_CLIENT_ID.items() if value == actor)
    return Client(Config({'office': ENDPOINT}, client_id, 'synthetic-test-secret'), opener)


class AdapterTests(unittest.TestCase):
    def test_real_client_output_retains_validated_payload(self):
        response = client(Opener({'message': receipt()})).send('office', PAYLOAD['text'], client_message_id=MID)
        self.assertEqual(response['text'], PAYLOAD['text'])
        self.assertEqual(response['kind'], PAYLOAD['kind'])
        self.assertEqual(adapt_send_result(MESSAGE, response).kind, 'STORED')

    def test_both_actors_and_replay_bind_every_field(self):
        for actor in ('agent:ti', 'agent:daube'):
            for replay in (False, True):
                opener = Opener({'message': receipt(actor), 'replayed': replay})
                message = replace(MESSAGE, principal=actor)
                result = MessengerTransport(client(opener, actor), 'office')(message)
                self.assertEqual(result.kind, 'STORED')
                self.assertEqual(result.principal, actor)
                self.assertEqual(result.payload_digest, message.digest)
                self.assertEqual(result.client_message_id, MID)
                self.assertEqual(result.room, 'council')
                self.assertEqual(json.loads(opener.calls[0].data), {**PAYLOAD, 'clientMessageId': MID})
                self.assertEqual(len(opener.calls), 1)

    def test_client_receipt_mutations_uncertain(self):
        for mutation in ({'from': 'founder'}, {'from': 'agent:daube'}, {'room': 'other'},
                         {'tenantId': 'other'}, {'text': 'different'}, {'kind': 'challenge'},
                         {'clientMessageId': 'other-client-id'}, {'id': ''}):
            with self.subTest(mutation=mutation):
                opener = Opener({'message': {**receipt(), **mutation}, 'replayed': True})
                self.assertEqual(MessengerTransport(client(opener), 'office')(MESSAGE).kind, 'UNKNOWN')
                self.assertEqual(len(opener.calls), 1)

    def test_adapter_each_missing_or_mismatched_binding(self):
        response = client(Opener({'message': receipt()})).send('office', PAYLOAD['text'], client_message_id=MID)
        for field in ('sender', 'room', 'tenantId', 'clientMessageId', 'text', 'kind', 'messageId', 'status', 'http'):
            for value in ((None, '', [], {}) if field == 'messageId' else (None, '', 'wrong', [], {})):
                with self.subTest(field=field, value=value):
                    self.assertEqual(adapt_send_result(MESSAGE, {**response, field: value}).kind, 'UNKNOWN')
            reduced = dict(response)
            reduced.pop(field)
            self.assertEqual(adapt_send_result(MESSAGE, reduced).kind, 'UNKNOWN')
        self.assertEqual(adapt_send_result(MESSAGE, {'status': 'STORED_BY_SERVER'}).kind, 'UNKNOWN')

    def test_malformed_and_contradictory_result_fields(self):
        response = client(Opener({'message': receipt()})).send('office', PAYLOAD['text'], client_message_id=MID)
        for mutation in ({'reason': []}, {'reason': {}}, {'authenticatedActor': 'founder'},
                         {'observedActor': 'agent:daube'}, {'http': True}):
            self.assertEqual(adapt_send_result(MESSAGE, {**response, **mutation}).kind, 'UNKNOWN')
        for value in (None, [], True, 'STORED_BY_SERVER'):
            self.assertEqual(adapt_send_result(MESSAGE, value).kind, 'UNKNOWN')

    def test_contradictory_status_denial_is_held(self):
        response = client(Opener({'message': receipt()})).send('office', PAYLOAD['text'], client_message_id=MID)
        for mutation in ({'reason': 'SERVICE_IDENTITY_DENIED'}, {'http': 403},
                         {'status': 'UNVERIFIED', 'reason': 'SERVICE_IDENTITY_MISMATCH', 'http': 403},
                         {'status': 'BLOCKED', 'reason': 'SERVICE_IDENTITY_DENIED', 'http': 201},
                         {'status': 'BLOCKED', 'reason': 'SERVICE_IDENTITY_UNREGISTERED', 'http': 403},
                         {'status': 'BLOCKED', 'reason': 'SERVICE_IDENTITY_MISMATCH', 'http': 403}):
            self.assertEqual(adapt_send_result(MESSAGE, {**response, **mutation}).kind, 'UNKNOWN')

    def test_unknown_malformed_or_wrong_principal_no_http(self):
        for principal in ('founder', '', None, [], {}, 'agent:daube'):
            with self.subTest(principal=principal):
                opener = Opener({'message': receipt()})
                result = MessengerTransport(client(opener), 'office')(replace(MESSAGE, principal=principal))
                self.assertEqual(result.kind, 'DENIED')
                self.assertEqual(opener.calls, [])
        opener = Opener({'message': receipt()})
        self.assertEqual(MessengerTransport(client(opener, client_id='unknown'), 'office')(MESSAGE).kind, 'DENIED')
        self.assertEqual(opener.calls, [])

    def test_wrong_room_or_noncanonical_payload_no_http(self):
        for message in (replace(MESSAGE, room='other'),
                        replace(MESSAGE, payload=json.dumps({'text': ' trim ', 'kind': 'text'}))):
            opener = Opener({'message': receipt()})
            self.assertNotEqual(MessengerTransport(client(opener), 'office')(message).kind, 'STORED')
            self.assertEqual(opener.calls, [])

    def test_post_commit_actor_conflict_or_transport_failure_unknown(self):
        for data in ({'message': receipt(), 'authenticatedActor': 'founder'}, TimeoutError(),
                     HTTPError(ENDPOINT, 502, 'bad gateway', {}, None)):
            opener = Opener(data)
            result = MessengerTransport(client(opener), 'office')(MESSAGE)
            self.assertEqual(result.kind, 'UNKNOWN')
            self.assertEqual(len(opener.calls), 1)

    def test_http_auth_denial_terminal(self):
        for status in (401, 403):
            opener = Opener(HTTPError(ENDPOINT, status, 'denied', {}, None))
            self.assertEqual(MessengerTransport(client(opener), 'office')(MESSAGE).kind, 'DENIED')

    def test_end_to_end_queue_unknown_never_retries(self):
        with tempfile.TemporaryDirectory() as directory:
            box = Outbox(directory)
            box.enqueue(MESSAGE.operation_id, MID, 'agent:ti', 'council', PAYLOAD)
            opener = Opener({'message': receipt(), 'authenticatedActor': 'founder'})
            transport = MessengerTransport(client(opener), 'office')
            self.assertEqual(box.run_once(transport), 'UNCERTAIN')
            self.assertEqual(box.run_once(transport), 'IDLE')
            self.assertEqual(len(opener.calls), 1)
            self.assertEqual(Outbox(directory).get(MESSAGE.operation_id)['state'], 'UNCERTAIN')

    def test_end_to_end_queue_stored_and_denied_no_retries(self):
        for data, state in (({'message': receipt()}, 'STORED'),
                            (HTTPError(ENDPOINT, 403, 'denied', {}, None), 'DENIED')):
            with tempfile.TemporaryDirectory() as directory:
                box = Outbox(directory)
                box.enqueue(MESSAGE.operation_id, MID, 'agent:ti', 'council', PAYLOAD)
                opener = Opener(data)
                transport = MessengerTransport(client(opener), 'office')
                self.assertEqual(box.run_once(transport), state)
                self.assertEqual(box.run_once(transport), 'IDLE')
                self.assertEqual(len(opener.calls), 1)
