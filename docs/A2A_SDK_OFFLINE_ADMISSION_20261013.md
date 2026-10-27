# BRIDGE² — Optional A2A SDK Client Contract (Draft, 13 October 2026)

**Project:** D’AUBE SONNTAG only. **Promotion:** DRAFT/HOLD, additive to BRIDGE² PR #28, not a release. **Owner:** existing BRIDGE² / D’AUBE assurance operators; no new runtime, task owner or payment authority.

## Why this tranche exists

Previous tranches proved deterministic offline AgentCard review, raw-response hashing, and one **external public validation API** canary through an already-connected cloud research service. None of those proves A2A agent task transport. This tranche prepares the official typed SDK request interface **without implementing outbound sends**. The smallest valuable advance is to eliminate a future proprietary A2A message encoder while retaining the existing D’AUBE permission and cost gates.

Official, pinned upstream: [`a2aproject/a2a-python` v1.2.2](https://github.com/a2aproject/a2a-python/tree/v1.2.2), tag commit `2f9e44af243df5c7c7a3da361c8d095324bcd5e3`, Apache-2.0 license. Version 1.2.2 was released October 3, 2026. The upstream sample implements `Message(role=Role.ROLE_USER, message_id=..., parts=[Part(text=...)])` then `SendMessageRequest(message=message)`. The upstream v1 `ClientConfig` supports `streaming`, `polling`, `supported_protocol_bindings`, and `accepted_output_modes`. [SDK source sample](https://github.com/a2aproject/a2a-python/blob/v1.2.2/samples/cli.py); [release notes](https://github.com/a2aproject/a2a-python/releases/tag/v1.2.2).

## Observed integration boundary

`src/daube_bridge/a2a_sdk_adapter.py` consumes **the existing** `cloud_peer.prepare_handoff(card, request, policy)`. That gate already checks an explicit zero-spend, offline-only policy; HTTPS host allowlist; supported A2A 1.0 binding and selected skill; PUBLIC_SYNTHETIC classification; source-rights attestation; bounded message text; and secret/contact patterns.

The adapter exposes three operations:

1. `plan_sdk_handoff(card, request, policy) -> dict`: emits an audit-friendly, deterministic no-network plan with a SHA-256 of the synthetic task text, a hashed request identifier, an idempotence-*tracking* UUID5 derived from the handoff digest, the exact proposed endpoint/transport/output mode, and explicit non-authority flags. Neither task text nor raw request identifier is returned in the printed plan.
2. `create_sdk_request(card, request, policy, sdk_types=None) -> a2a.types.SendMessageRequest`: creates a typed protobuf request from the official **optional** `a2a-sdk==1.2.2` package. The `sdk_types` test seam permits in-memory shape checks where the SDK cannot be installed. It never constructs a transport and never calls `send_message`.
3. `create_sdk_client_config(card, request, policy, sdk_client=None) -> a2a.client.ClientConfig`: constructs the non-streaming, non-polling configuration limited to the approved binding and output mode. It creates neither an SDK `Client` nor an HTTP client.

**Important:** deterministic message IDs support offline replay audits but do **not** imply provider-side deduplication. Provider hostname allowlisting in JSON alone does not prove TLS/DNS identity; a separate verified transport will need DNS rebinding protection, redirect denial, token-to-audience binding, timeouts, egress restrictions, response size limits, strict callback origin and compensation or reconciliation on ambiguous delivery.

## Run offline

After optional dependency admission (not automatically performed in this PR), the isolated installation contract is `python -m pip install -e '.[a2a]'`. It installs the reviewed SDK version only when explicitly selected; `a2a-sdk` is **not** added to BRIDGE² core runtime dependencies.

Without installing anything, the deterministic plan is available:

```bash
PYTHONPATH=src python -m daube_bridge.a2a_sdk_adapter \
  --card examples/collaboration/agent-card.synthetic.json \
  --request examples/collaboration/request.synthetic.json \
  --policy examples/collaboration/policy.synthetic.json

PYTHONPATH=src pytest -q \
  tests/test_sdk_adapter.py tests/test_cloud_peer.py tests/test_discovery_receipt.py
```

The command returns `SDK_PREPARED_NO_NETWORK`, always with `external_action_authorized=false`, `sdk_transport_executed=false`, `identity_verified=false`, and `provider_cost_usd=null`. No SDK import, outbound HTTP request or credential is required for the CLI's plan mode. A missing/mismatched installed SDK produces an explicit `SDKDependencyMissing` when a caller attempts to create the protobuf/config object, not a fake successful SDK result.

## TDD and verification record

- **RED #1:** the initial stub raised `NotImplementedError` in the first behavior test (`1 failed`, exit 1). The original missing-module collection error was **not** counted as meaningful RED evidence.
- **GREEN #1:** 13 newly added tests passed on a synthetic SDK facade. Tests exercise the same protobuf constructor shapes as the v1.2.2 official sample; **this is not the actual binary SDK**.
- **RED #2:** a synthetic request ID containing a contact-like string leaked verbatim from the plan. New test failed. Removing the raw request ID from the plan and providing `request_id_sha256` resolved this case.
- **GREEN #2:** 18 new tests passed. Test-only fixtures now load from the existing `examples/collaboration` tree (no cross-test imports). Combined scoped test suite: **128/128 PASS** on Python 3.13.5, offline. The adapter and tests passed Python AST parsing. No customer/partner content or payment data was used.
- No import or runtime conformance test against the real `a2a-sdk==1.2.2` wheel was possible inside the sandbox because the package is not installed and PyPI network/DNS is unavailable. Full BRIDGE² pytest/Ruff and hosted exact-head CI were not established by these focused results.

## Promotion gates and operating policy

The existing BRIDGE² GitHub Actions `main` workflow is **manual `workflow_dispatch` only**; hosted-runner issue [#26](https://github.com/daubesonntag-dotcom/daube-agent-bridge/issues/26) remains unresolved. Do not confuse earlier CodeRabbit status or local scoped tests with exact-head hosted CI.

To move from request construction to actual cloud agent task execution, a separate release gate must require:

- official SDK 1.2.2 installed and verified from pinned release/supply-chain records, plus a true SDK-level contract test against a mock server;
- verified endpoint DNS/TLS identity, trust-policy source, scopes, API terms, data retention and data-residency/consent, credential isolation, and properly token-scoped HTTP client;
- an **independent** approval/capability from the designated D’AUBE CABINET/authority source, not an input JSON boolean or AgentCard content;
- isolated synthetic canary, explicit maximum monetary spend, no redirects, bounded timeouts, no automatic retries, bounded request/response size, no streaming until audited, abort on cancellation and unknown delivery, and external response treated as untrusted;
- exact-head green CI/CodeQL, reviewer approval, rollback path and post-run receipt. No interface may promote its own local run to `PRODUCTION_ADMITTED` or money `SETTLED`.

**Non-goals:** no new agent infrastructure, public gateway, OAuth tokens, account setup, third-party expenses, autosending tasks, workflow scheduler, duplicate project CRM, or client messaging. Existing D’AUBE owner separation and AMADELI exclusion remain unchanged.

## Independent cloud package sanity check (public synthetic only)

A single-use cloud sandbox successfully installed the exact upstream `a2a-sdk==1.2.2` **with its required dependencies** and constructed a real `SendMessageRequest(Message(...))` and non-streaming `ClientConfig`. The JSON results showed expected HTTP+JSON binding and JSON output support; no SDK network client or remote task was created. Python runtime was 3.11.2. An earlier intentionally dependency-free install fetched the wheel but could not import it because `google.protobuf` was missing; that first attempt is recorded as BLOCKED rather than as a success.

The two isolated Firecrawl cloud checks consumed six already-included credits in aggregate, decreasing the balance from 427 to 421; both sessions were closed. As Firecrawl Zero Data Retention is not available, **only public synthetic strings** were used. This verifies upstream constructor behavior, not this repository's adapter against the wheel, nor a live remote A2A exchange. The included `scripts/verify_a2a_sdk_contract.py` is designed for a later **exact-source** offline integration verification using that official wheel.
