#!/usr/bin/env python3
"""D'AUBE <> Ti portable MCP Messenger. Python stdlib, no background daemon.

Private transport is Cloudflare Access *service identity*, not an interactive user login.
This client cannot bypass a disabled origin or a missing original machine grant.
"""
from __future__ import annotations
import json
import os
import re
import sys
import uuid
from dataclasses import dataclass
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError

ALLOWED_HOSTS = frozenset({"council.daubesonntag.com", "remote.daubesonntag.com", "office-origin.daubesonntag.com"})
ENDPOINT_RE = re.compile(r"^(?:/api/agent-chat/(?:rooms/council|machine/rooms/[a-f0-9-]{36})|/workspace/api/agent-chat/rooms/council)/messages$")
MSG_ID_RE = re.compile(r"^[A-Za-z0-9_-]{12,90}$")
MAX_RESPONSE_BYTES = 256 * 1024
APPROVED_ROUTES = {
    "council": "https://council.daubesonntag.com/agent-chat",
    "remote": "https://remote.daubesonntag.com/workspace/",
    "office": "https://office-origin.daubesonntag.com/agent-chat",
}

class MessengerError(Exception):
    def __init__(self, code: str, http: int | None = None):
        super().__init__(code)
        self.code, self.http = code, http

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

@dataclass(frozen=True)
class Config:
    endpoints: dict[str, str]
    client_id: str
    client_secret: str
    timeout: float = 8.0

    @classmethod
    def from_environment(cls):
        return cls(
            endpoints={
                "council": os.getenv("DAUBE_TI_COUNCIL_MESSENGER_ENDPOINT", "https://council.daubesonntag.com/api/agent-chat/rooms/council/messages").strip(),
                "remote": os.getenv("DAUBE_TI_REMOTE_MESSENGER_ENDPOINT", "https://remote.daubesonntag.com/workspace/api/agent-chat/rooms/council/messages").strip(),
                "office": os.getenv("DAUBE_TI_OFFICE_MESSENGER_ENDPOINT", "https://office-origin.daubesonntag.com/api/agent-chat/rooms/council/messages").strip(),
            },
            client_id=os.getenv("DAUBE_TI_CF_ACCESS_CLIENT_ID", ""),
            client_secret=os.getenv("DAUBE_TI_CF_ACCESS_CLIENT_SECRET", ""),
        )

def validate_endpoint(value: str) -> str:
    if not value:
        raise MessengerError("ENDPOINT_NOT_CONFIGURED")
    try:
        u = urlsplit(value)
    except ValueError as exc:
        raise MessengerError("ENDPOINT_INVALID") from exc
    if (u.scheme != "https" or u.hostname not in ALLOWED_HOSTS or u.port is not None
            or u.username or u.password or u.query or u.fragment or not ENDPOINT_RE.fullmatch(u.path)
            or u.netloc != u.hostname):
        raise MessengerError("ENDPOINT_NOT_ALLOWLISTED")
    return value

class Client:
    def __init__(self, config: Config, opener=None):
        self.config = config
        self.opener = opener or build_opener(NoRedirect)

    def _endpoint(self, surface: str) -> str:
        if surface not in self.config.endpoints:
            raise MessengerError("UNKNOWN_SURFACE")
        endpoint = validate_endpoint(self.config.endpoints[surface])
        expected_hosts = {
            "council": "council.daubesonntag.com",
            "remote": "remote.daubesonntag.com",
            "office": "office-origin.daubesonntag.com",
        }
        if urlsplit(endpoint).hostname != expected_hosts.get(surface):
            raise MessengerError("SURFACE_HOST_MISMATCH")
        return endpoint

    def _call(self, surface: str, method: str, payload=None):
        endpoint = self._endpoint(surface)
        if not (self.config.client_id and self.config.client_secret):
            raise MessengerError("SERVICE_IDENTITY_NOT_CONFIGURED")
        p = urlsplit(endpoint)
        headers = {
            "CF-Access-Client-Id": self.config.client_id,
            "CF-Access-Client-Secret": self.config.client_secret,
            "Accept": "application/json",
            "Cache-Control": "no-store",
            "User-Agent": "daube-ti-messenger-mcp/0.1",
        }
        body = None
        if method == "POST":
            headers["Content-Type"] = "application/json"
            headers["Origin"] = f"{p.scheme}://{p.netloc}"
            body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            if len(body) > 8192:
                raise MessengerError("BODY_TOO_LARGE")
        req = Request(endpoint, data=body, headers=headers, method=method)
        try:
            resp = self.opener.open(req, timeout=self.config.timeout)
            with resp:
                status = resp.status
                data = resp.read(MAX_RESPONSE_BYTES + 1)
        except HTTPError as exc:
            if 300 <= exc.code < 400:
                raise MessengerError("ACCESS_LOGIN_REDIRECT_BLOCKED", exc.code) from None
            if exc.code in (401, 403):
                raise MessengerError("SERVICE_IDENTITY_DENIED", exc.code) from None
            if exc.code == 404:
                raise MessengerError("MESSENGER_ROUTE_NOT_DEPLOYED", exc.code) from None
            if exc.code == 503:
                raise MessengerError("MESSENGER_BACKEND_DISABLED", exc.code) from None
            raise MessengerError("REMOTE_HTTP_FAILURE", exc.code) from None
        except (URLError, TimeoutError, OSError):
            raise MessengerError("TRANSPORT_UNREACHABLE") from None
        if not (200 <= status < 300):
            raise MessengerError("REMOTE_HTTP_FAILURE", status)
        if len(data) > MAX_RESPONSE_BYTES:
            raise MessengerError("RESPONSE_TOO_LARGE")
        try:
            result = json.loads(data)
        except (UnicodeError, ValueError):
            raise MessengerError("RESPONSE_NOT_JSON") from None
        if not isinstance(result, dict):
            raise MessengerError("RESPONSE_NOT_OBJECT")
        return status, result

    def status(self, surface: str) -> dict:
        try:
            status, result = self._call(surface, "GET")
            if not isinstance(result.get("messages"), list):
                raise MessengerError("MESSENGER_READ_CONTRACT_MISMATCH")
            return {"status": "READABLE", "surface": surface, "http": status, "messageCountReturned": len(result["messages"]), "canSendVerified": False}
        except MessengerError as e:
            return {"status": "BLOCKED", "surface": surface, "reason": e.code, "http": e.http}

    def send(self, surface: str, text: str, *, kind="text", client_message_id: str | None = None) -> dict:
        if not isinstance(text, str) or not text.strip() or len(text) > 4000:
            return {"status": "REJECTED", "reason": "TEXT_INVALID"}
        if kind not in ("text", "challenge"):
            return {"status": "REJECTED", "reason": "KIND_INVALID"}
        mid = client_message_id or str(uuid.uuid4())
        if not isinstance(mid, str) or not MSG_ID_RE.fullmatch(mid):
            return {"status": "REJECTED", "reason": "CLIENT_MESSAGE_ID_INVALID"}
        try:
            status, result = self._call(surface, "POST", {"text": text.strip(), "kind": kind, "clientMessageId": mid})
            msg = result.get("message")
            if (not isinstance(msg, dict) or not isinstance(msg.get("id"), str) or not msg["id"].strip()
                    or not isinstance(msg.get("from"), str) or not msg["from"].strip()
                    or msg.get("clientMessageId") != mid):
                raise MessengerError("SEND_RECEIPT_INVALID")
            # Sending and server persistence are not recipient delivery.
            return {"status": "STORED_BY_SERVER", "surface": surface, "http": status,
                    "messageId": msg["id"], "clientMessageId": mid,
                    "sender": msg.get("from"), "recipientReadVerified": False,
                    "replayed": bool(result.get("replayed", False))}
        except MessengerError as e:
            return {"status": "UNVERIFIED", "surface": surface, "reason": e.code,
                    "http": e.http, "clientMessageId": mid, "safeToRetryWithSameId": True}

    def read(self, surface: str, limit: int = 20) -> dict:
        if not isinstance(limit, int) or not 1 <= limit <= 100:
            return {"status": "REJECTED", "reason": "LIMIT_INVALID"}
        try:
            _, data = self._call(surface, "GET")
            messages = data.get("messages")
            if not isinstance(messages, list) or len(messages) > 1200:
                raise MessengerError("MESSENGER_READ_CONTRACT_MISMATCH")
            return {"status": "READABLE", "surface": surface, "messages": messages[-limit:],
                    "identityReadOnly": True}
        except MessengerError as e:
            return {"status": "BLOCKED", "surface": surface, "reason": e.code, "http": e.http}

    def verify_reply(self, surface: str, message_id: str, sender: str) -> dict:
        # The original persisted message must exist, with the exact sender.
        # Never interpret an unrelated actor or a missing reply ID as delivery.
        if (not isinstance(message_id, str) or not message_id.strip()
                or len(message_id) > 90 or not isinstance(sender, str) or not sender.strip()):
            return {"status": "REJECTED", "reason": "MESSAGE_ID_OR_SENDER_INVALID"}
        result = self.read(surface, limit=100)
        if result.get("status") != "READABLE":
            return result
        messages = result["messages"]
        original = next((m for m in messages if isinstance(m, dict)
                         and m.get("id") == message_id and m.get("from") == sender), None)
        if original is None:
            return {"status": "ORIGINAL_MESSAGE_NOT_VERIFIED", "messageId": message_id,
                    "cryptographicReceiptVerified": False}
        original_room = original.get("room")
        if not isinstance(original_room, str) or not original_room.strip():
            return {"status": "ORIGINAL_ROOM_NOT_VERIFIED", "messageId": message_id,
                    "cryptographicReceiptVerified": False}
        expected = {"agent:ti": "agent:daube", "agent:daube": "agent:ti"}
        counterpart = expected.get(sender)
        if counterpart is None:
            return {"status": "COUNTERPART_IDENTITY_NOT_CONFIGURED", "messageId": message_id,
                    "cryptographicReceiptVerified": False}
        for m in messages:
            if (isinstance(m, dict) and m.get("from") == counterpart
                    and isinstance(m.get("id"), str) and m["id"].strip()
                    and m.get("room") == original_room
                    and m.get("text") == "ACK " + message_id
                    and m.get("id") != message_id):
                return {"status": "COUNTERPART_ACK_VISIBLE", "messageId": message_id,
                        "replyId": m["id"], "from": counterpart,
                        "cryptographicReceiptVerified": False}
        return {"status": "AWAITING_COUNTERPART_REPLY", "messageId": message_id,
                "cryptographicReceiptVerified": False}

    def audit(self) -> dict:
        """Read-only self-inventory; NEVER equate a status probe with 2-party delivery."""
        reports = {surface: self.status(surface) for surface in ("council", "remote", "office")}
        has_machine_identity = bool(self.config.client_id and self.config.client_secret)
        checks = [
            {"check": "existing_machine_identity_configured", "state": "PASS" if has_machine_identity else "HOLD"},
            *({"check": surface + "_authorized_api_read",
               "state": "PASS" if reports[surface].get("status") == "READABLE" else "HOLD",
               "reason": reports[surface].get("reason")}
              for surface in ("council", "remote", "office")),
            {"check": "bidirectional_sender_recipient_readback", "state": "UNVERIFIED"}
        ]
        return {"schema": "daube.ti.messenger.capability-audit.v1",
                "status": "REPORT_ONLY", "surfaces": reports, "checks": checks,
                "operations": ["status", "send", "read", "verify_reply", "sites", "audit"],
                "signedMissionReceiptVerified": False,
                "bidirectionalDeliveryVerified": False,
                "productionMessengerReady": False}

TOOLS = [
    {"name": "daube_messenger_status", "description": "Check the existing D'AUBE Messenger transport without browser login; machine service identity required.",
     "inputSchema": {"type": "object", "properties": {"surface": {"type": "string", "enum": ["council", "remote", "office"]}}, "required": ["surface"]}},
    {"name": "daube_messenger_send", "description": "Send one idempotent text/challenge via existing Messenger. Does not claim recipient read or delivery.",
     "inputSchema": {"type": "object", "properties": {"surface": {"type": "string", "enum": ["council", "remote", "office"]}, "text": {"type": "string", "maxLength": 4000}, "kind": {"type": "string", "enum": ["text", "challenge"]}, "clientMessageId": {"type": "string"}}, "required": ["surface", "text"]}},
    {"name": "daube_messenger_read", "description": "Read only messages that existing D'AUBE Messenger allows this machine identity to read.",
     "inputSchema": {"type": "object", "properties": {"surface": {"type": "string", "enum": ["council", "remote", "office"]}, "limit": {"type": "integer", "minimum": 1, "maximum": 100}}, "required": ["surface"]}},
    {"name": "daube_messenger_verify_reply", "description": "Look for counterpart ACK <message-id> by a different persisted actor (not cryptographic mission receipt).",
     "inputSchema": {"type": "object", "properties": {"surface": {"type": "string", "enum": ["council", "remote", "office"]}, "messageId": {"type": "string"}, "sender": {"type": "string"}}, "required": ["surface", "messageId", "sender"]}},
    {"name": "daube_messenger_sites", "description": "Return Council, Remote and Office user-facing web links; these links can still require interactive Founder access.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "daube_messenger_audit", "description": "Live read-only capability inventory and PASS/HOLD/UNVERIFIED checks for Council, Remote, Office.",
     "inputSchema": {"type": "object", "properties": {}}},
]

def invoke(client, name, args):
    if not isinstance(args, dict):
        args = {}
    if name == "daube_messenger_sites":
        return {"status": "LINKS", "web": APPROVED_ROUTES, "noHumanLoginForMachineTransport": True,
                "machineServiceIdentityStillRequired": True}
    if name == "daube_messenger_status":
        return client.status(args.get("surface", ""))
    if name == "daube_messenger_audit":
        return client.audit()
    if name == "daube_messenger_send":
        return client.send(args.get("surface", ""), args.get("text"),
                           kind=args.get("kind", "text"), client_message_id=args.get("clientMessageId"))
    if name == "daube_messenger_read":
        return client.read(args.get("surface", ""), args.get("limit", 20))
    if name == "daube_messenger_verify_reply":
        return client.verify_reply(args.get("surface", ""), args.get("messageId"), args.get("sender"))
    raise MessengerError("UNKNOWN_TOOL")

def run_mcp(client):
    """MCP stdio JSON-RPC. No server, daemon, browser extension or external package."""
    for line in sys.stdin:
        try:
            msg = json.loads(line)
            if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0":
                continue
            method, mid = msg.get("method"), msg.get("id")
            if method == "notifications/initialized" or mid is None:
                continue
            if method == "initialize":
                value = {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}},
                         "serverInfo": {"name": "daube-ti-messenger", "version": "0.1.0"}}
            elif method == "ping":
                value = {}
            elif method == "tools/list":
                value = {"tools": TOOLS}
            elif method == "tools/call":
                params = msg.get("params") or {}
                out = invoke(client, params.get("name"), params.get("arguments") or {})
                value = {"content": [{"type": "text", "text": json.dumps(out, ensure_ascii=False)}],
                         "isError": out.get("status") in {"REJECTED", "BLOCKED", "UNVERIFIED"}}
            else:
                raise MessengerError("METHOD_NOT_FOUND")
            ans = {"jsonrpc": "2.0", "id": mid, "result": value}
        except Exception as exc:
            ans = {"jsonrpc": "2.0", "id": msg.get("id") if isinstance(locals().get("msg"), dict) else None,
                   "error": {"code": -32603, "message": exc.code if isinstance(exc, MessengerError) else "MCP_INTERNAL_ERROR"}}
        sys.stdout.write(json.dumps(ans, separators=(",", ":"), ensure_ascii=False) + "\n")
        sys.stdout.flush()

if __name__ == "__main__":
    run_mcp(Client(Config.from_environment()))
