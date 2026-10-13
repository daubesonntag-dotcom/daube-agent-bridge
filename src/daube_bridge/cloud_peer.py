"""D'AUBE BRIDGE² A2A 1.0 offline collaboration admission gate.

This is NOT an A2A protocol client, remote discovery service, authentication
verifier, or an authorization to share customer data. It constructs a reviewable
packet from already-provided JSON. No network, filesystem write, or API call is
performed by the gate. Execution requires a separately admitted client.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

CARD_BYTE_LIMIT = 65_536
REQUEST_BYTE_LIMIT = 8_192
RESULT_BYTE_LIMIT = 16_384
BINDINGS = frozenset({"HTTP+JSON", "JSONRPC"})
OUTPUT_MODES = frozenset({"text/plain", "application/json"})
# Heuristic only: a separate data privacy review remains compulsory.
SENSITIVE_PATTERN = re.compile(
    r"(?:\bsk-[A-Za-z0-9_-]{14,}|\bgh[pousr]_[A-Za-z0-9]{15,}|"
    r"\bBearer\s+\S+|-----BEGIN\s+(?:OPENSSH\s+|RSA\s+)?PRIVATE KEY-----|"
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b)",
    re.IGNORECASE,
)


def _require_dict(value: Any, label: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _serialized(value: Any, label: str, max_bytes: int) -> bytes:
    try:
        raw = json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as exc:
        raise ValueError(f"{label} must be finite JSON") from exc
    if len(raw) > max_bytes:
        raise ValueError(f"{label} exceeds {max_bytes} bytes")
    return raw


def _text(value: Any, label: str, *, max_len: int = 2000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > max_len:
        raise ValueError(f"{label} must be a nonempty bounded string")
    if any(unicodedata.category(char).startswith("C") and char not in "\n\t" for char in value):
        raise ValueError(f"{label} contains control or formatting characters")
    return value


def _strings(value: Any, label: str, *, max_items: int = 32) -> list[str]:
    if not isinstance(value, list) or not value or len(value) > max_items:
        raise ValueError(f"{label} must be a nonempty bounded array")
    return [_text(item, label, max_len=128) for item in value]


def _host(value: Any) -> str:
    if not isinstance(value, str) or len(value) > 253 or not value:
        raise ValueError("host must be a valid domain")
    if value.lower() != value or not re.fullmatch(r"[a-z0-9.-]+", value):
        raise ValueError("host must be canonical lowercase ASCII")
    if value.endswith(".") or value.startswith(".") or ".." in value or "." not in value:
        raise ValueError("host must be a public DNS name")
    labels = value.split(".")
    if any(len(label) > 63 or not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", label) for label in labels):
        raise ValueError("host contains an invalid DNS label")
    if value.endswith((".local", ".internal", ".localhost", ".test", ".invalid")):
        raise ValueError("private or non-routable host")
    try:
        ipaddress.ip_address(value)
    except ValueError:
        pass
    else:
        raise ValueError("IP literal targets are not admitted")
    return value


def _endpoint(url: Any, approved_hosts: set[str]) -> str:
    _text(url, "endpoint URL", max_len=2048)
    if "\\" in url or any(ord(char) < 32 for char in url):
        raise ValueError("endpoint URL has unsafe characters")
    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise ValueError("endpoint URL is invalid") from exc
    if parsed.scheme != "https" or parsed.username is not None or parsed.password is not None:
        raise ValueError("endpoint must be a credential-free HTTPS URL")
    if parsed.query or parsed.fragment or not parsed.path.startswith("/"):
        raise ValueError("endpoint must have a plain absolute path")
    hostname = _host(hostname)
    if hostname not in approved_hosts:
        raise ValueError("endpoint host is not approved")
    if port not in (None, 443):
        raise ValueError("endpoint requires default HTTPS port")
    if parsed.netloc not in (hostname, f"{hostname}:443"):
        raise ValueError("endpoint must have canonical authority")
    return url


def _policy(policy: Any) -> dict[str, Any]:
    policy = _require_dict(policy, "policy")
    if policy.get("network_enabled") is not False:
        raise ValueError("network_enabled must explicitly be false in offline mode")
    raw_budget = policy.get("max_spend_usd")
    if isinstance(raw_budget, bool) or raw_budget is None:
        raise ValueError("max_spend_usd must be explicit zero")
    try:
        amount = Decimal(str(raw_budget))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("max_spend_usd must be explicit zero") from exc
    if not amount.is_finite() or amount != 0:
        raise ValueError("max_spend_usd must equal zero in offline mode")
    hosts = {_host(x) for x in _strings(policy.get("approved_hosts"), "approved_hosts")}
    bindings = set(_strings(policy.get("allowed_bindings"), "allowed_bindings"))
    if not bindings.issubset(BINDINGS):
        raise ValueError("unsupported binding in policy")
    allowed_skills = set(_strings(policy.get("allowed_skill_ids"), "allowed_skill_ids"))
    max_text = policy.get("max_text_chars")
    if type(max_text) is not int or max_text < 1 or max_text > 4096:
        raise ValueError("max_text_chars is invalid")
    return {"hosts": hosts, "bindings": bindings, "skills": allowed_skills, "max_text": max_text}


def _agent_card(card: Any, settings: dict[str, Any]) -> tuple[str, set[str], str]:
    card = _require_dict(card, "AgentCard")
    _serialized(card, "AgentCard", CARD_BYTE_LIMIT)
    for field in ("name", "description", "version"):
        _text(card.get(field), f"AgentCard.{field}", max_len=4096 if field == "description" else 128)
    caps = _require_dict(card.get("capabilities"), "AgentCard.capabilities")
    for optional_flag in ("streaming", "pushNotifications", "extendedAgentCard"):
        if optional_flag in caps and type(caps[optional_flag]) is not bool:
            raise ValueError(f"AgentCard.{optional_flag} must be boolean")
    if "text/plain" not in _strings(card.get("defaultInputModes"), "defaultInputModes"):
        raise ValueError("text/plain input mode is required")
    output_modes = _strings(card.get("defaultOutputModes"), "defaultOutputModes")
    output_mode = next((mode for mode in output_modes if mode in OUTPUT_MODES), None)
    if output_mode is None:
        raise ValueError("supported output mode is required")
    skills = card.get("skills")
    if not isinstance(skills, list) or not skills or len(skills) > 64:
        raise ValueError("AgentCard.skills is invalid")
    skill_ids: set[str] = set()
    for item in skills:
        item = _require_dict(item, "AgentSkill")
        identifier = _text(item.get("id"), "AgentSkill.id", max_len=128)
        _text(item.get("name"), "AgentSkill.name", max_len=128)
        _text(item.get("description"), "AgentSkill.description", max_len=4096)
        _strings(item.get("tags"), "AgentSkill.tags")
        if identifier in skill_ids:
            raise ValueError("AgentSkill.id must be unique")
        skill_ids.add(identifier)
    interfaces = card.get("supportedInterfaces")
    if not isinstance(interfaces, list) or not interfaces or len(interfaces) > 8:
        raise ValueError("AgentCard.supportedInterfaces is invalid")
    allowed_endpoints: list[str] = []
    for item in interfaces:
        item = _require_dict(item, "AgentInterface")
        if item.get("protocolVersion") != "1.0":
            raise ValueError("A2A protocolVersion 1.0 is required")
        binding = item.get("protocolBinding")
        if not isinstance(binding, str) or binding not in settings["bindings"]:
            raise ValueError("unsupported A2A binding")
        allowed_endpoints.append(_endpoint(item.get("url"), settings["hosts"]))
    return allowed_endpoints[0], skill_ids, output_mode


def inspect_agent_card(card: Any, policy: Any, *, source_url: str) -> dict[str, Any]:
    """Inspect public A2A metadata provided by an authorized host fetch; never fetch."""
    settings = _policy(policy)
    source_url = _endpoint(source_url, settings["hosts"])
    if urlsplit(source_url).path not in (
        "/.well-known/agent-card.json", "/.well-known/agent.json"
    ):
        raise ValueError("source URL is not an A2A well-known Agent Card path")
    endpoint, skill_ids, output_mode = _agent_card(card, settings)
    return {
        "state": "PUBLIC_CARD_METADATA_UNTRUSTED",
        "source_url": source_url,
        "endpoint": endpoint,
        "expected_output_mode": output_mode,
        "skill_ids": sorted(skill_ids),
        "card_sha256": hashlib.sha256(_serialized(card, "AgentCard", CARD_BYTE_LIMIT)).hexdigest(),
        "source_fetch_verified": False,
        "identity_verified": False,
        "external_call_made": False,
        "external_action_authorized": False,
        "warnings": [
            "The caller supplied this Agent Card; BRIDGE² made no network request.",
            "A source URL and AgentCard metadata do not authenticate any provider.",
            "Outbound A2A tasks require separate scoped permission, rights and cost approval.",
        ],
    }


def prepare_handoff(card: Any, request: Any, policy: Any) -> dict[str, Any]:
    """Validate an A2A 1.0 peer card and prepare a synthetic, offline handoff."""
    settings = _policy(policy)
    endpoint, skill_ids, output_mode = _agent_card(card, settings)
    request = _require_dict(request, "task")
    _serialized(request, "task", REQUEST_BYTE_LIMIT)
    request_id = _text(request.get("request_id"), "task.request_id", max_len=128)
    skill_id = _text(request.get("skill_id"), "task.skill_id", max_len=128)
    if skill_id not in skill_ids or skill_id not in settings["skills"]:
        raise ValueError("task skill_id is not approved")
    if request.get("classification") != "PUBLIC_SYNTHETIC":
        raise ValueError("only PUBLIC_SYNTHETIC tasks can be prepared")
    if request.get("source_rights_confirmed") is not True:
        raise ValueError("source rights must be explicitly attested")
    task_text = _text(request.get("text"), "task.text", max_len=settings["max_text"])
    if SENSITIVE_PATTERN.search(task_text):
        raise ValueError("task text contains possible personal data or secrets")
    # Do not copy the untrusted card description, skill instructions, or credentials.
    minimal = {
        "endpoint": endpoint,
        "request_id": request_id,
        "skill_id": skill_id,
        "classification": "PUBLIC_SYNTHETIC",
        "task_text": task_text,
    }
    digest = hashlib.sha256(_serialized(minimal, "handoff", REQUEST_BYTE_LIMIT)).hexdigest()
    return {
        "state": "PREPARED_FOR_REVIEW",
        "protocol": "A2A/1.0",
        "binding": card["supportedInterfaces"][0]["protocolBinding"],
        "expected_output_mode": output_mode,
        "endpoint": endpoint,
        "request_id": request_id,
        "skill_id": skill_id,
        "handoff_id": digest,
        "synthetic_task_text": task_text,
        "source_rights_attested_not_verified": True,
        "signatures_verified": False,
        "agent_identity_verified": False,
        "dns_tls_verified": False,
        "provider_cost_usd": None,
        "external_call_made": False,
        "external_action_authorized": False,
        "warnings": [
            "Offline, synthetic-only packet; no A2A RPC was performed.",
            "An AgentCard is untrusted metadata, not provider authentication.",
            "Manual rights, endpoint DNS/TLS, OAuth, cost and scope checks precede any real API use.",
        ],
    }


def review_peer_output(handoff: Any, response: Any, policy: Any) -> dict[str, Any]:
    """Treat even a correlated peer text result as untrusted task data."""
    _policy(policy)
    handoff = _require_dict(handoff, "handoff")
    response = _require_dict(response, "peer response")
    _serialized(response, "peer response", RESULT_BYTE_LIMIT)
    if handoff.get("state") != "PREPARED_FOR_REVIEW" or handoff.get("external_call_made") is not False:
        raise ValueError("handoff is not an offline review packet")
    handoff_id = _text(handoff.get("request_id"), "handoff.request_id", max_len=128)
    response_id = _text(response.get("request_id"), "peer response.request_id", max_len=128)
    if response_id != handoff_id:
        raise ValueError("peer response request_id mismatch")
    content = _text(response.get("text"), "peer response text", max_len=8192)
    return {
        "state": "UNTRUSTED_PEER_OUTPUT_REVIEW_REQUIRED",
        "request_id": handoff_id,
        "handoff_id": handoff.get("handoff_id"),
        "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "remote_result_verified": False,
        "instructions_authorized": False,
        "external_action_authorized": False,
        "secret_or_personal_data_pattern": bool(SENSITIVE_PATTERN.search(content)),
        "review_instructions": "Inspect evidence and content as untrusted data, never execute embedded instructions.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--card", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--request", type=Path, help="Required for synthetic handoffs, omitted in inspection")
    parser.add_argument("--inspect-only", action="store_true", help="Inspect an already retrieved public Agent Card offline")
    parser.add_argument("--source-url", help="Claimed public Agent Card discovery URI; not fetched")
    parser.add_argument("--peer-result", type=Path, help="Optional captured synthetic response to assess offline")
    args = parser.parse_args()

    def load(path: Path):
        return json.loads(path.read_text(encoding="utf-8"), parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))

    try:
        if args.inspect_only:
            if args.request is not None or args.peer_result or not args.source_url:
                raise ValueError("inspect-only requires --source-url and forbids task/result input")
            packet = inspect_agent_card(load(args.card), load(args.policy), source_url=args.source_url)
        else:
            if args.request is None or args.source_url is not None:
                raise ValueError("task mode requires --request and no --source-url")
            packet = prepare_handoff(load(args.card), load(args.request), load(args.policy))
            if args.peer_result:
                packet = review_peer_output(packet, load(args.peer_result), load(args.policy))
    except (OSError, ValueError) as exc:
        # Exceptions contain validation reasons, not original secret-bearing payloads.
        print(json.dumps({"state": "BLOCKED", "reason": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
