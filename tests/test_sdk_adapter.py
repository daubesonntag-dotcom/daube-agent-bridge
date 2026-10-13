"""SDK 1.2.2 shape tests; no actual SDK, socket, credential or remote agent."""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from daube_bridge import a2a_sdk_adapter as sdk
FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "examples" / "collaboration"


def _load_fixture(name):
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def example_card():
    return _load_fixture("agent-card.synthetic.json")


def example_policy():
    return _load_fixture("policy.synthetic.json")


def example_request():
    return _load_fixture("request.synthetic.json")


class Part:
    def __init__(self, *, text):
        self.text = text


class Role:
    ROLE_USER = 1


class Message:
    def __init__(self, *, role, message_id, parts):
        self.role = role
        self.message_id = message_id
        self.parts = parts


class SendMessageRequest:
    def __init__(self, *, message):
        self.message = message


class ClientConfig:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


FAKE_PROTO = SimpleNamespace(Part=Part, Role=Role, Message=Message, SendMessageRequest=SendMessageRequest)
FAKE_CLIENT = SimpleNamespace(ClientConfig=ClientConfig)


def test_plan_is_bounded_no_network_no_authority_or_private_task_leak():
    card, req, policy = example_card(), example_request(), example_policy()
    original = copy.deepcopy((card, req, policy))
    plan = sdk.plan_sdk_handoff(card, req, policy)
    assert plan["state"] == "SDK_PREPARED_NO_NETWORK"
    assert plan["sdk_dependency"] == "a2a-sdk==1.2.2"
    assert plan["endpoint"] == "https://agent.example.com/a2a/v1"
    assert plan["binding"] == "HTTP+JSON"
    assert plan["streaming"] is False
    assert plan["sdk_transport_executed"] is False
    assert plan["identity_verified"] is False
    assert plan["external_action_authorized"] is False
    assert plan["provider_cost_usd"] is None
    assert plan["input_sha256"] and len(plan["input_sha256"]) == 64
    assert plan["message_id"].count("-") == 4
    assert req["text"] not in json.dumps(plan)
    assert plan == sdk.plan_sdk_handoff(card, req, policy)
    assert (card, req, policy) == original


def test_sdk_request_materialization_uses_actual_documented_proto_field_shapes():
    data = sdk.create_sdk_request(example_card(), example_request(), example_policy(), sdk_types=FAKE_PROTO)
    assert isinstance(data, SendMessageRequest)
    assert data.message.role == Role.ROLE_USER
    assert len(data.message.parts) == 1
    assert data.message.parts[0].text == example_request()["text"]
    assert data.message.message_id == sdk.plan_sdk_handoff(example_card(), example_request(), example_policy())["message_id"]


def test_config_disables_streaming_polling_and_fixes_allowed_binding():
    cfg = sdk.create_sdk_client_config(example_card(), example_request(), example_policy(), sdk_client=FAKE_CLIENT)
    assert cfg.kwargs["streaming"] is False
    assert cfg.kwargs["polling"] is False
    assert cfg.kwargs["supported_protocol_bindings"] == ["HTTP+JSON"]
    assert cfg.kwargs["accepted_output_modes"] == ["text/plain"]


def test_message_id_changes_when_task_id_or_body_changes():
    x = sdk.plan_sdk_handoff(example_card(), example_request(), example_policy())
    req = example_request()
    req["request_id"] = "independent-request"
    y = sdk.plan_sdk_handoff(example_card(), req, example_policy())
    req2 = example_request()
    req2["text"] = "Another synthetic onboarding comparison."
    z = sdk.plan_sdk_handoff(example_card(), req2, example_policy())
    assert len({x["message_id"], y["message_id"], z["message_id"]}) == 3


@pytest.mark.parametrize("field,value", [
    ("classification", "CUSTOMER_CONFIDENTIAL"),
    ("source_rights_confirmed", False),
    ("skill_id", "not-authorized"),
    ("text", "Contact private-person@example.com"),
])
def test_unsafe_tasks_never_become_sdk_requests(field, value):
    req = example_request()
    req[field] = value
    with pytest.raises(ValueError):
        sdk.create_sdk_request(example_card(), req, example_policy(), sdk_types=FAKE_PROTO)


def test_policy_cannot_enable_network_or_positive_spend():
    for key, value in [("network_enabled", True), ("max_spend_usd", "0.01")]:
        policy = example_policy()
        policy[key] = value
        with pytest.raises(ValueError):
            sdk.create_sdk_client_config(example_card(), example_request(), policy, sdk_client=FAKE_CLIENT)


def test_sdk_missing_uses_explicit_unavailable_not_fake_proto():
    with pytest.raises(sdk.SDKDependencyMissing):
        sdk.create_sdk_request(example_card(), example_request(), example_policy())


def test_rejects_old_protocol_and_unapproved_host():
    card = example_card()
    card["supportedInterfaces"][0]["protocolVersion"] = "0.3"
    with pytest.raises(ValueError):
        sdk.plan_sdk_handoff(card, example_request(), example_policy())
    card = example_card()
    card["supportedInterfaces"][0]["url"] = "https://unknown.example.net/a2a"
    with pytest.raises(ValueError):
        sdk.plan_sdk_handoff(card, example_request(), example_policy())


def test_cli_default_prints_dry_run_only(tmp_path):
    for name, value in [("card",example_card()),("policy",example_policy()),("request",example_request())]:
        (tmp_path/f"{name}.json").write_text(json.dumps(value),encoding="utf-8")
    cmd=[sys.executable,"-m","daube_bridge.a2a_sdk_adapter", "--card",str(tmp_path/"card.json"),"--request",str(tmp_path/"request.json"),"--policy",str(tmp_path/"policy.json")]
    p=subprocess.run(cmd,capture_output=True,text=True,check=False)
    assert p.returncode==0,p.stderr
    reply=json.loads(p.stdout)
    assert reply["state"]=="SDK_PREPARED_NO_NETWORK"
    assert reply["external_action_authorized"] is False
    assert example_request()["text"] not in p.stdout


def test_cli_bad_task_fails_closed_without_traceback(tmp_path):
    req=example_request();req["classification"]="SECRET"
    for name,value in [("card",example_card()),("policy",example_policy()),("request",req)]:
        (tmp_path/f"{name}.json").write_text(json.dumps(value),encoding="utf-8")
    cmd=[sys.executable,"-m","daube_bridge.a2a_sdk_adapter", "--card",str(tmp_path/"card.json"),"--request",str(tmp_path/"request.json"),"--policy",str(tmp_path/"policy.json")]
    p=subprocess.run(cmd,capture_output=True,text=True,check=False)
    assert p.returncode==2
    assert json.loads(p.stdout)["state"]=="BLOCKED"
    assert "Traceback" not in p.stderr


def test_plan_redacts_raw_request_identifier_even_if_contact_string():
    req = example_request()
    req["request_id"] = "private-contact@example.org"
    plan = sdk.plan_sdk_handoff(example_card(), req, example_policy())
    assert "request_id" not in plan
    assert len(plan["request_id_sha256"]) == 64
    assert "private-contact@example.org" not in json.dumps(plan)


def test_json_output_peer_uses_sdk_json_result_config():
    card = example_card()
    card["defaultOutputModes"] = ["application/json"]
    cfg = sdk.create_sdk_client_config(card, example_request(), example_policy(), sdk_client=FAKE_CLIENT)
    assert cfg.kwargs["accepted_output_modes"] == ["application/json"]


def test_sdk_pin_version_drift_fails_closed(monkeypatch):
    monkeypatch.setattr(sdk, "version", lambda _: "1.1.5")
    with pytest.raises(sdk.SDKDependencyMissing, match="pinned"):
        sdk.create_sdk_request(example_card(), example_request(), example_policy())


def test_prepare_injected_sdk_types_never_creates_network_connections(monkeypatch):
    import socket
    def forbid(*args, **kwargs):
        raise AssertionError("network access is prohibited")
    monkeypatch.setattr(socket, "create_connection", forbid)
    monkeypatch.setattr(socket.socket, "connect", forbid)
    sdk.plan_sdk_handoff(example_card(), example_request(), example_policy())
    sdk.create_sdk_request(example_card(), example_request(), example_policy(), sdk_types=FAKE_PROTO)
    sdk.create_sdk_client_config(example_card(), example_request(), example_policy(), sdk_client=FAKE_CLIENT)


def test_task_sending_is_not_exposed_by_offline_sdk_module():
    assert not hasattr(sdk, "send_sdk_message")
    assert not hasattr(sdk, "create_live_sdk_client")
