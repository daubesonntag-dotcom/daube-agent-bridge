import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ti_messenger_mcp as m

ENDPOINT = "https://office-origin.daubesonntag.com/api/agent-chat/rooms/council/messages"
C = m.Config(endpoints={"office": ENDPOINT, "council": "", "remote": ""}, client_id="existing-client-id", client_secret="unit-test-secret")

class Response:
    def __init__(self, status, payload):
        self.status = status
        self.body = io.BytesIO(json.dumps(payload).encode())
    def __enter__(self): return self
    def __exit__(self, *args): return None
    def read(self, size): return self.body.read(size)

class Opener:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []
    def open(self, req, timeout=0):
        self.calls.append((req, timeout))
        reply = self.responses.pop(0)
        if isinstance(reply, Exception): raise reply
        return reply

class TestMessenger(unittest.TestCase):
    def test_allowlisted_existing_origin(self):
        self.assertEqual(m.validate_endpoint(ENDPOINT), ENDPOINT)

    def test_reject_arbitrary_domain_and_http(self):
        for url in ["http://office-origin.daubesonntag.com/api/agent-chat/rooms/council/messages",
                    "https://evil.example/api/agent-chat/rooms/council/messages",
                    "https://office-origin.daubesonntag.com:444/api/agent-chat/rooms/council/messages",
                    "https://office-origin.daubesonntag.com/api/agent-chat/rooms/council/messages?secret=1",
                    "https://user:pass@office-origin.daubesonntag.com/api/agent-chat/rooms/council/messages"]:
            with self.subTest(url=url), self.assertRaises(m.MessengerError): m.validate_endpoint(url)

    def test_empty_council_and_remote_are_not_fabricated(self):
        c=m.Client(C)
        for surface in ["council","remote"]:
            self.assertEqual(c.status(surface)["reason"], "ENDPOINT_NOT_CONFIGURED")

    def test_missing_service_credentials_fail_closed(self):
        c=m.Client(m.Config({"office": ENDPOINT},"", ""))
        self.assertEqual(c.status("office")["reason"],"SERVICE_IDENTITY_NOT_CONFIGURED")

    def test_read_genuine_message_list(self):
        o=Opener(Response(200,{"messages":[{"id":"a","from":"ti"},{"id":"b","from":"daube"}]}))
        data=m.Client(C,o).read("office",1)
        self.assertEqual(data["status"],"READABLE")
        self.assertEqual(data["messages"],[{"id":"b","from":"daube"}])
        req=o.calls[0][0]
        self.assertEqual(req.get_method(),"GET")
        self.assertEqual(req.get_header("Cf-access-client-id"),"existing-client-id")

    def test_send_persisted_receipt_is_not_delivery(self):
        mid="f4c0cb24-1f01-4fb2-b781-1d5df9367f80"
        r=Response(201,{"message":{"id":"msg-server-1","clientMessageId":mid,"from":"agent:ti"},"replayed":False,"agentDelivered":False})
        o=Opener(r)
        data=m.Client(C,o).send("office","Xin chào D'AUBE",client_message_id=mid)
        self.assertEqual(data["status"],"STORED_BY_SERVER")
        self.assertFalse(data["recipientReadVerified"])
        self.assertEqual(data["clientMessageId"],mid)
        req=o.calls[0][0]
        self.assertEqual(req.get_header("Origin"),"https://office-origin.daubesonntag.com")
        self.assertEqual(json.loads(req.data)["clientMessageId"],mid)

    def test_identical_request_id_can_retry(self):
        mid="d4e6f45f-3e27-455e-aab2-2233dceb98d6"
        o=Opener(Response(200,{"message":{"id":"msg-1","clientMessageId":mid},"replayed":True}))
        self.assertTrue(m.Client(C,o).send("office","same",client_message_id=mid)["replayed"])

    def test_unverified_send_returns_retry_id(self):
        mid="de4d77a8-4b6c-41cb-ad8e-113edbab813a"
        o=Opener(HTTPError(ENDPOINT,503,"service disabled",{},None))
        data=m.Client(C,o).send("office","please deliver",client_message_id=mid)
        self.assertEqual(data["status"],"UNVERIFIED")
        self.assertEqual(data["clientMessageId"],mid)
        self.assertEqual(data["reason"],"MESSENGER_BACKEND_DISABLED")

    def test_login_redirect_does_not_count_as_ready(self):
        o=Opener(HTTPError(ENDPOINT,302,"redirect",{"Location":"https://access.example/login"},None))
        self.assertEqual(m.Client(C,o).status("office")["reason"],"ACCESS_LOGIN_REDIRECT_BLOCKED")

    def test_forbidden_denies_and_never_echoes_secret(self):
        o=Opener(HTTPError(ENDPOINT,403,"unit-test-secret",{},None))
        data=m.Client(C,o).status("office")
        self.assertEqual(data["reason"],"SERVICE_IDENTITY_DENIED")
        self.assertNotIn("unit-test-secret",json.dumps(data))

    def test_invalid_success_shape_does_not_count_as_stored(self):
        o=Opener(Response(201,{"ok":True,"message":{"id":"unverified-id","clientMessageId":"wrong-id"}}))
        self.assertEqual(m.Client(C,o).send("office","test")["status"],"UNVERIFIED")

    def test_login_html_200_does_not_count_as_readable(self):
        o=Opener(Response(200,{"unrelated":"login"}))
        self.assertEqual(m.Client(C,o).status("office")["reason"],"MESSENGER_READ_CONTRACT_MISMATCH")

    def test_invalid_message_rejected_before_network(self):
        o=Opener()
        c=m.Client(C,o)
        self.assertEqual(c.send("office"," ")["status"],"REJECTED")
        self.assertEqual(c.send("office","a"*4001)["status"],"REJECTED")
        self.assertEqual(c.send("office","ok",kind="privileged")['status'],"REJECTED")
        self.assertEqual(len(o.calls),0)

    def test_reply_from_same_sender_not_recipient_evidence(self):
        o=Opener(Response(200,{"messages":[{"id":"reply","from":"ti","text":"ACK msg-1"}]}))
        self.assertEqual(m.Client(C,o).verify_reply("office","msg-1","agent:ti")["status"],"ORIGINAL_MESSAGE_NOT_VERIFIED")

    def test_reply_from_other_sender_is_observation_not_signature(self):
        o=Opener(Response(200,{"messages":[{"id":"msg-1","from":"agent:ti","room":"council","text":"hello"},{"id":"reply","from":"agent:daube","room":"council","text":"ACK msg-1"}]}))
        result=m.Client(C,o).verify_reply("office","msg-1","agent:ti")
        self.assertEqual(result['status'],"COUNTERPART_ACK_VISIBLE")
        self.assertFalse(result['cryptographicReceiptVerified'])


    def test_ack_requires_exact_counterpart_and_original(self):
        original={"id":"msg-1","from":"agent:ti","room":"council","text":"hello"}
        for fake in [
            {"id":"reply","from":"random-actor","room":"council","text":"ACK msg-1"},
            {"id":"","from":"agent:daube","room":"council","text":"ACK msg-1"},
            {"id":"reply","from":"agent:daube","room":"other","text":"ACK msg-1"},
            {"id":"reply","from":"agent:daube","text":"ACK msg-1"},
        ]:
            o=Opener(Response(200,{"messages":[original,fake]}))
            self.assertEqual(m.Client(C,o).verify_reply("office","msg-1","agent:ti")["status"],"AWAITING_COUNTERPART_REPLY")

    def test_send_rejects_missing_server_message_id_or_sender(self):
        for message in [
            {"id":"","from":"agent:ti","clientMessageId":"client-id-123456"},
            {"id":"message-id-123456","from":"","clientMessageId":"client-id-123456"},
            {"id":"message-id-123456","clientMessageId":"client-id-123456"},
        ]:
            o=Opener(Response(201,{"message":message}))
            self.assertEqual(m.Client(C,o).send("office","hello",client_message_id="client-id-123456")["status"],"UNVERIFIED")

    def test_mcp_jsonrpc_handshake_and_discovery(self):
        data='\n'.join(map(json.dumps,[{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}},
                                   {"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}},
                                   {"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"daube_messenger_status","arguments":{"surface":"remote"}}}]))+'\n'
        out=io.StringIO(); old=sys.stdin
        try:
            sys.stdin=io.StringIO(data)
            with redirect_stdout(out): m.run_mcp(m.Client(C))
        finally: sys.stdin=old
        values=[json.loads(line) for line in out.getvalue().splitlines()]
        self.assertEqual(values[0]["result"]["protocolVersion"],"2025-06-18")
        self.assertEqual(len(values[1]["result"]["tools"]),5)
        self.assertTrue(values[2]["result"]["isError"])

if __name__ == '__main__': unittest.main()
