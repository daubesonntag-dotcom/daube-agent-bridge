# D'AUBE // BRIDGE² — Public A2A Discovery Receipt and Cloud Canary

**As of:** 13 October 2026  
**Status:** Source-only `DRAFT / HOLD`; additive review tranche for existing [BRIDGE² PR #28](https://github.com/daubesonntag-dotcom/daube-agent-bridge/pull/28).  
**Scope:** D'AUBE only. No production deployment, secrets, purchase, customer transfer, custom provider account or new runtime owner.

## Problem, verified context and smallest reusable solution

The previous `inspect_agent_card()` validates JSON already supplied by an operator, but a changed or poisoned download might be inadvertently treated as the same agent. A fetched document is not equivalent to a trusted, authenticated provider. The existing BRIDGE² compiler and offline peer gate remain the owner of portable skills and A2A preparation.

This addition implements `inspect_discovery_http()` in the **same** `src/daube_bridge/cloud_peer.py` module. It consumes an already-fetched **exact bytes** response, explicitly supplied HTTP status/content type/redirect count, an allowlisted offline policy and an optional previous raw SHA-256. It NEVER fetches a URL, calls a model, authorizes a task, verifies a TLS connection, accepts payment or writes financial/CRM/customer data.

### Contract

- `body_bytes`: nonempty raw bytes, maximum 65,536 bytes. Strict UTF-8, no BOM. Reject malformed JSON, nonfinite numbers and duplicate keys at any depth.
- `source_url`: canonical HTTPS, no credentials, query or fragment; exactly `/.well-known/agent-card.json` or legacy `/.well-known/agent.json`. The source hostname must match the approved advertised A2A interface hostname for this conservative single-host pilot.
- `status_code`: exact integer 200; a truthy boolean, string `"200"` or redirect status does not count.
- `content_type`: `application/a2a+json` (preferred) or `application/json` with optional UTF-8 charset; reject HTML and embedded HTTP control characters.
- `redirect_count`: explicitly supplied integer **zero**; no automatic follow-up to a redirected site.
- `policy`: the existing BRIDGE² host/binding/skill allowlist with `network_enabled=false` and `max_spend_usd=0`.
- `previous_digest`: optional, valid lowercase 64-hex raw SHA-256. A different downloaded byte sequence yields `PUBLIC_CARD_CHANGED_REVIEW_REQUIRED`. Unknown previous digest is **unknown**, not `unchanged`.

Output records `card_raw_sha256` over **received bytes**, `card_sha256` over the existing normalized JSON object, byte count, source, selected A2A endpoint, skills and output mode, MIME/status/redirect metadata and drift. `source_fetch_verified=false`, `identity_verified=false`, `external_action_authorized=false` and `external_call_made=false` always remain false: the HTTP metadata is **caller-supplied**, not cryptographically attested by this library. A matching hash proves only that two received byte strings match, NOT that a particular organization authored them.

### Safe CLI example

```bash
PYTHONPATH=src python -m daube_bridge.cloud_peer \
  --card examples/collaboration/agent-card.synthetic.json \
  --policy examples/collaboration/policy.synthetic.json \
  --inspect-fetched-card \
  --source-url https://agent.example.com/.well-known/agent-card.json \
  --http-status 200 \
  --content-type application/a2a+json \
  --redirect-count 0
```

The example uses the reserved `example.com` domain and fake HTTP observations. This is **NOT** a successful network read. When using an authorized cloud fetch, save its untouched response bytes to a private/isolated workspace and pass the actual accompanying transport metadata. Do not paste account cookies, tokens or third-party data into a URL. A third-party scraper's reported status and MIME must still be interpreted as its claims; BRIDGE² does not itself prove network provenance. In case of a missing status, unknown redirect chain, content truncation, changed card or unapproved endpoint: **HOLD**, not an optimistic inferred pass.

## One real external public API canary

On 13 October 2026, the connected cloud Firecrawl session performed **one** documented public beta request to AgentCard.net's HTTP+JSON skill endpoint `POST https://www.agentcard.net/api/agent-card`, with `skillId=validate-agent-card` and a **fictional** `D'AUBE Synthetic Validator Peer` card. No real D'AUBE runtime credentials, client names, or internal project code were submitted. External response: **HTTP 200**, JSON `validation.valid=true`, nine validation passes, and warnings to declare authentication if required and to add provider metadata for marketplace readiness. The fictional card's external `inspectorScore` was **69/100 (grade C)**. This score is NOT a security audit of D'AUBE, a contract, or proof of collaboration with a general-purpose LLM.

Firecrawl credits went from 431 to 428 (three **existing** credits consumed for the single browser canary); the cloud session was explicitly stopped. Its Zero Data Retention option is not available to this team. No new subscription, paid model or payment rail was provisioned. An additional public GET of AgentCard.net's well-known Agent Card reported HTTP 200, `application/a2a+json` and returned syntactically valid card data; raw byte-level authenticity is not independently cryptographically verified here.

Official public sources: [A2A Protocol 1.0 specification](https://a2a-protocol.org/v1.0.0/specification/), [AgentCard.net API](https://www.agentcard.net/agent-card-api), [MCP 2026-07-28 authorization security](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/basic/authorization/security-considerations.mdx). Public API beta terms, pricing, rate limits and auth requirements may change: recheck before a future call. No network request to that provider is executed by committed BRIDGE² code in this tranche.

## QA receipts and stop conditions

- **TDD RED:** 53 expected new-test failures prior to implementation; 54 focused checks green after implementation. Later three HTTP header-injection tests failed before patch and all passed after a minimal validation change.
- **Current focused local test:** 110/110 passed under Python 3.13.5; `python -m compileall -q src/daube_bridge tests` passed. A separate seeded 2,048-case malformed discovery fuzz run returned 1,754 controlled rejections, 294 untrusted accepts, **zero unhandled exceptions**, and zero accepted cases with elevated external authority. These checks do not prove an entire production security posture.
- **Full repository tests and lint:** Not run as part of this isolated addon; local sandbox lacks the existing project's FastMCP and Ruff dependencies. GitHub Actions `main` is manually triggered only and hosted runner issue [#26](https://github.com/daubesonntag-dotcom/daube-agent-bridge/issues/26) remains a blocker. `CodeRabbit success` or resolved comments do not replace exact-head CI.
- **Release:** keep PR #28 `DRAFT/HOLD`; do not merge, publish a live A2A server, add new payment providers, send client data or automatically call third-party AI. Real live orchestration requires explicit service terms and consent, least-privilege authentication, allowed data, a hard provider cost cap and tenant separation, DNS/TLS/redirect verification by the actual transport, verified response correlation, idempotency controls, sandbox E2E and an approved runtime owner.

**Next step recommendation:** add a separately admitted, bounded transport behind the existing offline preparation/review interface, only after exact-head CI and security authorization. Prefer the official Apache-2.0 [A2A Python SDK](https://github.com/a2aproject/a2a-python) over reimplementing the protocol. Do not promote a fetched Agent Card into credentials, task execution or commercial authority.
