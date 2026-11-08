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
C = m.Config(endpoints={"office": ENDPOINT, "council": "", "remote": ""}, client_id="8ceae31b13c0a5f495c8374e6a8aced4.access", client_secret="unit-test-secret")

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

    def test_canonical_council_remote_endpoints_accepted(self):
        c = m.Client(m.Config(endpoints={
            "council": "https://council.daubesonntag.com/api/agent-chat/rooms/council/messages",
            "remote": "https://remote.daubesonntag.com/workspace/api/agent-chat/rooms/council/messages",
            "office": ENDPOINT},
            client_id="8ceae31b13c0a5f495c8374e6a8aced4.access", client_secret="unit-test-secret"), Opener())
        self.assertIn("/workspace/api/agent-chat", c._endpoint("remote"))
        self.assertEqual(m.validate_endpoint(c._endpoint("council")), c._endpoint("council"))

    def test_cross_surface_endpoint_mismatch_is_denied(self):
        config = m.Config(endpoints={
            "council": "https://remote.daubesonntag.com/workspace/api/agent-chat/rooms/council/messages",
            "remote": "https://council.daubesonntag.com/api/agent-chat/rooms/council/messages",
            "office": ENDPOINT},
            client_id="8ceae31b13c0a5f495c8374e6a8aced4.access", client_secret="unit-test-secret")
        client = m.Client(config, Opener())
        for surface in ("council", "remote"):
            result = client.status(surface)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result["reason"], "SURFACE_HOST_MISMATCH")

    def test_remote_wrong_path_is_rejected(self):
        for endpoint in (
            "https://remote.daubesonntag.com/api/agent-chat/rooms/council/messages?token=x",
            "https://remote.daubesonntag.com/workspace/api/agent-chat/rooms/admin/messages",
        ):
            with self.assertRaises(m.MessengerError):
                m.validate_endpoint(endpoint)

    def test_empty_council_and_remote_are_not_fabricated(self):
        c=m.Client(C)
        for surface in ["council","remote"]:
            self.assertEqual(c.status(surface)["reason"], "ENDPOINT_NOT_CONFIGURED")

    def test_missing_service_credentials_fail_closed(self):
        c=m.Client(m.Config({"office": ENDPOINT},"", ""))
        self.assertEqual(c.status("office")["reason"],"SERVICE_IDENTITY_NOT_CONFIGURED")

    def test_read_genuine_message_list(self):
        o=Opener(Response(200,{"authenticatedActor":"agent:ti","room":"council","messages":[{"id":"a","from":"ti"},{"id":"b","from":"daube"}]}))
        data=m.Client(C,o).read("office",1)
        self.assertEqual(data["status"],"READABLE")
        self.assertEqual(data["messages"],[{"id":"b","from":"daube"}])
        req=o.calls[0][0]
        self.assertEqual(req.get_method(),"GET")
        self.assertEqual(req.get_header("Cf-access-client-id"),"8ceae31b13c0a5f495c8374e6a8aced4.access")

    def test_send_persisted_receipt_is_not_delivery(self):
        mid="f4c0cb24-1f01-4fb2-b781-1d5df9367f80"
        r=Response(201,{"message":{"id":"msg-server-1","clientMessageId":mid,"from":"agent:ti","room":"council","tenantId":"daube","text":"Xin chào D\u0027AUBE","kind":"text"},"replayed":False,"agentDelivered":False})
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
        o=Opener(Response(200,{"message":{"id":"msg-1","from":"agent:ti","clientMessageId":mid,"room":"council","tenantId":"daube","text":"same","kind":"text"},"replayed":True}))
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
        o=Opener(Response(200,{"authenticatedActor":"agent:ti","room":"council","messages":[{"id":"reply","from":"ti","text":"ACK msg-1"}]}))
        self.assertEqual(m.Client(C,o).verify_reply("office","msg-1","agent:ti")["status"],"ORIGINAL_MESSAGE_NOT_VERIFIED")

    def test_reply_from_other_sender_is_observation_not_signature(self):
        o=Opener(Response(200,{"authenticatedActor":"agent:ti","room":"council","messages":[{"id":"msg-1","from":"agent:ti","room":"council","text":"hello"},{"id":"reply","from":"agent:daube","room":"council","text":"ACK msg-1"}]}))
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
            o=Opener(Response(200,{"authenticatedActor":"agent:ti","room":"council","messages":[original,fake]}))
            self.assertEqual(m.Client(C,o).verify_reply("office","msg-1","agent:ti")["status"],"AWAITING_COUNTERPART_REPLY")

    def test_send_rejects_missing_server_message_id_or_sender(self):
        for message in [
            {"id":"","from":"agent:ti","clientMessageId":"client-id-123456"},
            {"id":"message-id-123456","from":"","clientMessageId":"client-id-123456"},
            {"id":"message-id-123456","clientMessageId":"client-id-123456"},
        ]:
            o=Opener(Response(201,{"message":message}))
            self.assertEqual(m.Client(C,o).send("office","hello",client_message_id="client-id-123456")["status"],"UNVERIFIED")

    def test_ack_rejects_both_missing_or_empty_room(self):
        for room in [None, "", "   "]:
            original = {"id":"msg-1","from":"agent:ti","text":"hello"}
            ack = {"id":"reply-1","from":"agent:daube","text":"ACK msg-1"}
            if room is not None:
                original["room"] = room
                ack["room"] = room
            o = Opener(Response(200,{"authenticatedActor":"agent:ti","room":"council","messages":[original,ack]}))
            result = m.Client(C,o).verify_reply("office","msg-1","agent:ti")
            self.assertEqual(result["status"],"ORIGINAL_ROOM_NOT_VERIFIED")

    def test_audit_is_an_inventory_not_mission_or_delivery_proof(self):
        config=m.Config(endpoints={"council":"","remote":"","office":ENDPOINT},
                        client_id="",client_secret="")
        result=m.Client(config,Opener()).audit()
        self.assertEqual(result["status"],"REPORT_ONLY")
        self.assertEqual(result["schema"],"daube.ti.messenger.capability-audit.v1")
        self.assertFalse(result["bidirectionalDeliveryVerified"])
        self.assertFalse(result["productionMessengerReady"])
        self.assertTrue(all(x["state"]!="PASS" for x in result["checks"]))
        self.assertEqual(m.invoke(m.Client(config,Opener()),"daube_messenger_audit",{})["status"],"REPORT_ONLY")

    def test_audit_positive_read_is_not_e2e_pass(self):
        o=Opener(Response(200,{"authenticatedActor":"agent:ti","room":"council","messages":[]}))
        config=m.Config(endpoints={"office":ENDPOINT,"council":"","remote":""},
                        client_id="8ceae31b13c0a5f495c8374e6a8aced4.access",client_secret="unit-test-secret")
        report=m.Client(config,o).audit()
        self.assertEqual(report["surfaces"]["office"]["status"],"READABLE")
        self.assertFalse(report["productionMessengerReady"])
        self.assertEqual(report["checks"][-1]["state"],"UNVERIFIED")

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
        self.assertEqual(len(values[1]["result"]["tools"]),6)
        self.assertTrue(values[2]["result"]["isError"])


    def test_reject_noncanonical_text_before_network(self):
        o = Opener()
        result = m.Client(C, o).send("office", " padded ", client_message_id="d4e6f45f-3e27-455e-aab2-2233dceb98d6")
        self.assertEqual(result["status"], "REJECTED")
        self.assertEqual(result["reason"], "TEXT_INVALID_OR_NOT_CANONICAL")
        self.assertEqual(o.calls, [])

    def test_denied_write_never_auto_retries(self):
        mid = "d4e6f45f-3e27-455e-aab2-2233dceb98d6"
        o = Opener(HTTPError(ENDPOINT, 403, "denied", {}, None))
        result = m.Client(C, o).send("office", "hello", client_message_id=mid)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["reason"], "SERVICE_IDENTITY_DENIED")
        self.assertFalse(result["safeToRetryWithSameId"])
        self.assertEqual(result["nextAction"], "RESTORE_AUTHORIZATION")

    def test_ambiguous_503_requires_cold_read_before_retry(self):
        mid = "d4e6f45f-3e27-455e-aab2-2233dceb98d6"
        o = Opener(HTTPError(ENDPOINT, 503, "upstream unavailable", {}, None))
        result = m.Client(C, o).send("office", "hello", client_message_id=mid)
        self.assertEqual(result["status"], "UNVERIFIED")
        self.assertFalse(result["safeToRetryWithSameId"])
        self.assertEqual(result["nextAction"], "COLD_READ_BY_UUID_BEFORE_SAME_PAYLOAD_RETRY")

    def test_reject_forged_sender_or_room_tenant_kind_payload(self):
        mid = "d4e6f45f-3e27-455e-aab2-2233dceb98d6"
        good = {"id": "server-id", "from": "agent:ti", "clientMessageId": mid,
                "room": "council", "tenantId": "daube", "text": "hello", "kind": "text"}
        for changes in ({"from": "agent:daube"}, {"room": "revenue"}, {"tenantId": "other"},
                        {"text": "different"}, {"kind": "challenge"}):
            forged = {**good, **changes}
            o = Opener(Response(201, {"message": forged, "replayed": False}))
            config = m.Config({"office": ENDPOINT},
                              "8ceae31b13c0a5f495c8374e6a8aced4.access", "unit-test-secret")
            result = m.Client(config, o).send("office", "hello", client_message_id=mid)
            self.assertEqual(result["status"], "UNVERIFIED", changes)
            self.assertEqual(result["reason"], "SEND_RECEIPT_INVALID", changes)
            self.assertFalse(result["safeToRetryWithSameId"])

    def test_status_does_not_invent_machine_identity(self):
        config = m.Config({"office": ENDPOINT},
                          "8ceae31b13c0a5f495c8374e6a8aced4.access", "unit-test-secret")
        result = m.Client(config, Opener(Response(200, {"room": "council", "messages": []}))).status("office")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["reason"], "SERVICE_IDENTITY_UNVERIFIED")
        self.assertNotIn("observedActor", result)
        same = m.Client(config, Opener(Response(200, {
            "room": "council", "messages": [], "authenticatedActor": "agent:ti"}))).status("office")
        self.assertTrue(same["actorMatchesExpected"])


    def test_unknown_machine_identity_never_reaches_http(self):
        mid = "client-id-123456"
        config = m.Config({"office": ENDPOINT}, "unregistered-id", "unit-test-secret")
        for sender in ("founder", "agent:ti", "agent:daube"):
            receipt = {"message": {"id": "server-id", "from": sender,
                       "clientMessageId": mid, "room": "council", "tenantId": "daube",
                       "text": "hello", "kind": "text"}}
            o = Opener(Response(201, receipt))
            c = m.Client(config, o)
            for result in (c.send("office", "hello", client_message_id=mid),
                           c.status("office"), c.read("office")):
                self.assertEqual(result["status"], "BLOCKED")
                self.assertEqual(result["reason"], "SERVICE_IDENTITY_UNREGISTERED")
            self.assertEqual(o.calls, [])

    def test_read_and_status_require_observed_expected_actor(self):
        for actor in (None, "", " ", [], {}, "agent:daube", "founder", "agent:ti "):
            for operation in ("read", "status"):
                with self.subTest(actor=actor, operation=operation):
                    payload = {"room": "council", "messages": [], "authenticatedActor": actor}
                    result = getattr(m.Client(C, Opener(Response(200, payload))), operation)("office")
                    self.assertEqual(result["status"], "BLOCKED")
                    self.assertNotIn("messages", result)
                    self.assertIn(result["reason"], ("SERVICE_IDENTITY_UNVERIFIED", "SERVICE_IDENTITY_MISMATCH"))
        for operation in ("read", "status"):
            result = getattr(m.Client(C, Opener(Response(200, {"room": "council", "messages": []}))), operation)("office")
            self.assertEqual(result["reason"], "SERVICE_IDENTITY_UNVERIFIED")

    def test_both_registered_actors_require_exact_read_binding(self):
        for client_id, actor in m.ACTOR_BY_ACCESS_CLIENT_ID.items():
            for operation in ("read", "status"):
                config = m.Config({"office": ENDPOINT}, client_id, "unit-test-secret")
                payload = {"room": "council", "messages": [], "authenticatedActor": actor}
                result = getattr(m.Client(config, Opener(Response(200, payload))), operation)("office")
                self.assertEqual(result["status"], "READABLE")
                self.assertEqual(result["observedActor"], actor)
                self.assertTrue(result["actorMatchesExpected"])

    def test_send_rejects_conflicting_observed_actor(self):
        mid = "client-id-123456"
        for actor in (None, "", "founder", "agent:daube"):
            payload = {"authenticatedActor": actor, "message": {
                "id": "server-id", "from": "agent:ti", "clientMessageId": mid,
                "room": "council", "tenantId": "daube", "text": "hello", "kind": "text"}}
            o = Opener(Response(201, payload))
            result = m.Client(C, o).send("office", "hello", client_message_id=mid)
            self.assertEqual(result["status"], "UNVERIFIED")
            self.assertFalse(result["safeToRetryWithSameId"])
            self.assertEqual(result["nextAction"], "COLD_READ_BY_UUID_BEFORE_SAME_PAYLOAD_RETRY")
            self.assertEqual(len(o.calls), 1)

    def test_replay_requires_exact_identity_and_payload_binding(self):
        mid = "client-id-123456"
        for client_id, actor in m.ACTOR_BY_ACCESS_CLIENT_ID.items():
            config = m.Config({"office": ENDPOINT}, client_id, "unit-test-secret")
            good = {"id": "server-id", "from": actor, "clientMessageId": mid,
                    "room": "council", "tenantId": "daube", "text": "hello", "kind": "text"}
            other = "agent:daube" if actor == "agent:ti" else "agent:ti"
            for mutation in ({}, {"from": "founder"}, {"from": other},
                             {"text": "different"}, {"kind": "challenge"},
                             {"room": "other"}, {"tenantId": "other"},
                             {"clientMessageId": "different-id-1234"}):
                o = Opener(Response(200, {"message": {**good, **mutation}, "replayed": True}))
                result = m.Client(config, o).send("office", "hello", client_message_id=mid)
                self.assertEqual(result["status"], "UNVERIFIED" if mutation else "STORED_BY_SERVER")
                if mutation:
                    self.assertEqual(result["reason"], "SEND_RECEIPT_INVALID")
                    self.assertFalse(result["safeToRetryWithSameId"])
                else:
                    self.assertTrue(result["replayed"])

    def test_audit_does_not_admit_unverified_read_or_unknown_identity(self):
        for actor in (None, "founder", "agent:daube"):
            o = Opener(Response(200, {"room": "council", "messages": [], "authenticatedActor": actor}))
            report = m.Client(C, o).audit()
            check = next(x for x in report["checks"] if x["check"] == "office_authorized_api_read")
            self.assertEqual(check["state"], "HOLD")
        o = Opener()
        config = m.Config({"office": ENDPOINT}, "unregistered-id", "unit-test-secret")
        report = m.Client(config, o).audit()
        self.assertEqual(report["checks"][0]["state"], "HOLD")
        self.assertEqual(o.calls, [])


if __name__ == '__main__': unittest.main()
