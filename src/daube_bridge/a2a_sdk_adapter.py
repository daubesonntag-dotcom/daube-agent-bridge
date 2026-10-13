"""D'AUBE BRIDGE2 A2A SDK 1.2.2 *offline* protobuf request adapter.

Prepare one bounded, PUBLIC_SYNTHETIC message using the upstream A2A SDK
message types. No transport is created and no network, auth or persistence is
performed. Approval for real sends is deliberately NOT represented here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import uuid
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from .cloud_peer import prepare_handoff

SDK_DISTRIBUTION = "a2a-sdk"
SDK_VERSION = "1.2.2"


class SDKDependencyMissing(RuntimeError):
    """The required pinned official SDK is unavailable or has changed."""


def _receipt(card: Any, request: Any, policy: Any) -> dict[str, Any]:
    """Re-evaluate all existing D'AUBE privacy/capability/cost boundaries."""
    return prepare_handoff(card, request, policy)


def _id(handoff_id: str) -> str:
    # Stable within an offline review for replay auditing. This is NOT a
    # guarantee that a remote A2A service deduplicates a repeated send.
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"daube-bridge2:a2a-v1:{handoff_id}"))


def plan_sdk_handoff(card: Any, request: Any, policy: Any) -> dict[str, Any]:
    """Describe exact SDK wiring without emitting user-supplied task content."""
    packet = _receipt(card, request, policy)
    return {
        "state": "SDK_PREPARED_NO_NETWORK",
        "sdk_dependency": f"{SDK_DISTRIBUTION}=={SDK_VERSION}",
        "protocol": packet["protocol"],
        "endpoint": packet["endpoint"],
        "binding": packet["binding"],
        "expected_output_mode": packet["expected_output_mode"],
        "request_id_sha256": hashlib.sha256(packet["request_id"].encode("utf-8")).hexdigest(),
        "message_id": _id(packet["handoff_id"]),
        "handoff_id": packet["handoff_id"],
        "input_sha256": hashlib.sha256(packet["synthetic_task_text"].encode("utf-8")).hexdigest(),
        "streaming": False,
        "polling": False,
        "identity_verified": False,
        "provider_cost_usd": None,
        "sdk_transport_executed": False,
        "external_action_authorized": False,
        "credential_embedded": False,
        "response_trusted": False,
        "warnings": [
            "Synthetic protobuf request preparation is not a network A2A connection.",
            "Deterministic message_id does not guarantee provider-side idempotency.",
            "SDK package version, provider identity, remote rights and spending require separate admission.",
        ],
    }


def _sdk(modulename: str, injectable: Any) -> Any:
    if injectable is not None:
        return injectable  # Test seam for offline protocol-shape verification only.
    try:
        installed = version(SDK_DISTRIBUTION)
    except PackageNotFoundError as exc:
        raise SDKDependencyMissing("a2a-sdk==1.2.2 is not installed (optional extra)") from exc
    if installed != SDK_VERSION:
        raise SDKDependencyMissing("A2A SDK version is not pinned to 1.2.2")
    try:
        if modulename == "types":
            from a2a import types as sdk_module
        else:
            from a2a import client as sdk_module
    except ImportError as exc:
        raise SDKDependencyMissing("Installed A2A SDK imports are unavailable") from exc
    return sdk_module


def create_sdk_request(
    card: Any, request: Any, policy: Any, *, sdk_types: Any = None,
) -> Any:
    """Construct A2A v1 SendMessageRequest protobuf; *never* send it.

    Official v1.2.2 documented fields: Message(role=ROLE_USER, message_id,
    parts=[Part(text=...)]), SendMessageRequest(message=message).
    """
    packet = _receipt(card, request, policy)
    types = _sdk("types", sdk_types)
    message = types.Message(
        role=types.Role.ROLE_USER,
        message_id=_id(packet["handoff_id"]),
        parts=[types.Part(text=packet["synthetic_task_text"])],
    )
    return types.SendMessageRequest(message=message)


def create_sdk_client_config(
    card: Any, request: Any, policy: Any, *, sdk_client: Any = None,
) -> Any:
    """Construct non-streaming SDK ClientConfig; never create a client/transport."""
    packet = _receipt(card, request, policy)
    client = _sdk("client", sdk_client)
    return client.ClientConfig(
        streaming=False,
        polling=False,
        supported_protocol_bindings=[packet["binding"]],
        accepted_output_modes=[packet["expected_output_mode"]],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--card", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    args = parser.parse_args()

    def read(file: Path) -> Any:
        return json.loads(file.read_text(encoding="utf-8"), parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))

    try:
        result = plan_sdk_handoff(read(args.card), read(args.request), read(args.policy))
    except (ValueError, OSError, UnicodeError) as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
