"""Explicit source-only adapter; reuses Client.send, never adds a transport.

Only trusted Client results are inputs. Field checks are not signature proofs.
The supported server contract is tenant daube / room council only.
"""
import hashlib
import json

from outbox import Result, classify_legacy_response
from ti_messenger_mcp import MessengerError


def _payload(message):
    payload = json.loads(message.payload)
    if (not isinstance(payload, dict) or set(payload) != {'text', 'kind'}
            or not isinstance(payload['text'], str) or not payload['text']
            or payload['text'] != payload['text'].strip()
            or len(payload['text']) > 4000 or payload['kind'] not in ('text', 'challenge')):
        raise ValueError('invalid canonical payload')
    return payload


def adapt_send_result(message, response):
    """Map validated persisted fields to outbox Result; never emits NOT_SENT."""
    if not isinstance(response, dict):
        return Result('UNKNOWN')
    if 'reason' in response and not isinstance(response['reason'], str):
        return Result('UNKNOWN')
    # Only exact existing-client denial shapes are terminal. Contradictory
    # success/denial fields may follow a committed write and must be held.
    reason, http = response.get('reason'), response.get('http')
    if response.get('status') == 'BLOCKED':
        if any(field in response for field in ('messageId', 'sender', 'room', 'tenantId', 'text', 'kind')):
            return Result('UNKNOWN')
        preflight = reason in (
            'SERVICE_IDENTITY_NOT_CONFIGURED', 'SERVICE_IDENTITY_UNREGISTERED',
            'SURFACE_HOST_MISMATCH',
        ) and http is None
        denied = reason == 'SERVICE_IDENTITY_DENIED' and type(http) is int and http in (401, 403)
        redirect = reason == 'ACCESS_LOGIN_REDIRECT_BLOCKED' and type(http) is int and 300 <= http < 400
        return Result('DENIED' if preflight or denied or redirect else 'UNKNOWN')
    if 'reason' in response:
        return Result('UNKNOWN')
    try:
        payload = _payload(message)
    except (ValueError, TypeError):
        return Result('UNKNOWN')
    if (message.principal not in ('agent:ti', 'agent:daube')
            or message.room != 'council'
            or response.get('status') != 'STORED_BY_SERVER'
            or type(response.get('http')) is not int
            or not 200 <= response['http'] < 300
            or any(field in response and response[field] != message.principal
                   for field in ('authenticatedActor', 'observedActor'))
            or response.get('sender') != message.principal
            or response.get('room') != message.room
            or response.get('tenantId') != 'daube'
            or response.get('clientMessageId') != message.client_message_id
            or response.get('text') != payload['text']
            or response.get('kind') != payload['kind']
            or not isinstance(response.get('messageId'), str)
            or not response['messageId'].strip()
            or len(response['messageId']) > 256):
        return Result('UNKNOWN')
    # Digest derives from returned persisted payload, not a blind copy of input.
    persisted = json.dumps({'text': response['text'], 'kind': response['kind']},
                           sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    digest = hashlib.sha256(persisted.encode()).hexdigest()
    if digest != message.digest:
        return Result('UNKNOWN')
    return Result('STORED', response['sender'], response['room'],
                  response['clientMessageId'], digest, response['messageId'])


class MessengerTransport:
    """Explicit injection into run_once; no loop, scheduler, credentials or I/O at init."""
    def __init__(self, client, surface):
        self.client = client
        self.surface = surface

    def __call__(self, message):
        # Reject unknown/mismatched queued principals before calling send/HTTP.
        if message.principal not in ('agent:ti', 'agent:daube') or message.room != 'council':
            return Result('DENIED')
        try:
            if self.client._expected_actor() != message.principal:
                return Result('DENIED')
            payload = _payload(message)
        except MessengerError as exc:
            return classify_legacy_response({'reason': exc.code, 'http': exc.http})
        except (ValueError, TypeError):
            return Result('UNKNOWN')
        response = self.client.send(self.surface, payload['text'], kind=payload['kind'],
                                    client_message_id=message.client_message_id)
        return adapt_send_result(message, response)
