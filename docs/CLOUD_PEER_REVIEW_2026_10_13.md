# D'AUBE BRIDGE² — Cloud Peer Interoperability Review (13 October 2026)

**Owner:** BRIDGE² maintainer / D'AUBE technical security reviewer.  
**Status:** `DRAFT / OFFLINE_POC / NOT_PRODUCTION_ADMITTED`.  
**Scope:** D'AUBE reusable public interoperability tooling. It does not import Amadeli source, customer credentials, proprietary AI prompts or private work evidence.

## Why this exists

D'AUBE BRIDGE² already compiles portable AI tool/skill specs for MCP, OpenAI, Claude, Gemini, DeepSeek, Llama and browsers. Compiling a compatible tool schema is not the same as securely *collaborating* with an independent remote agent. A2A adds an agent-to-agent exchange protocol; MCP remains the tool/data interface. Neither makes credentials, agent identity, inference quota or lawful data rights appear automatically.

This additive tranche provides a **purely offline** A2A v1 AgentCard admission and synthetic task packet to prepare later A2A/cloud integration. This is NOT a conforming A2A client/server, a remote Agent Card fetcher, a production peer handshake, or a certificate of provider trust. It never sends HTTP, calls an LLM, reads local secrets or schedules cloud jobs. `https://agent.example.com` is a **reserved example address**, not an actual reachable or endorsed partner.

### Grounded current standards

- [A2A 1.0.0 specification](https://a2a-protocol.org/v1.0.0/specification/), AgentCard §4.4 and security §13. Use `supportedInterfaces` containing `{url, protocolBinding, protocolVersion}`; the v0.3 `url`-only structure is not admitted by this narrow gate.
- [A2A discovery and extended cards](https://a2a-protocol.org/latest/topics/agent-discovery/): cards are unauthenticated metadata unless independently verified; sensitive extended cards require strong access control.
- [MCP 2026-07-28](https://blog.modelcontextprotocol.io/posts/2026-07-28/): stateless tool/data substrate, authorization issuer validation and enterprise-managed flows. Do not embed an obsolete MCP handshake assumption in a new cloud transport.
- [Cloudflare Workers official limits](https://developers.cloudflare.com/workers/platform/limits/): optional serverless candidate; capacity and billing depend on actual account, deployment, model and current free-tier limits. No cloud account changed here.

## Offline verification

From a Python 3.11+ checkout, with only stdlib for this standalone module:

```bash
python -m daube_bridge.cloud_peer \
  --card examples/collaboration/agent-card.synthetic.json \
  --policy examples/collaboration/policy.synthetic.json \
  --request examples/collaboration/request.synthetic.json

python -m daube_bridge.cloud_peer \
  --card examples/collaboration/agent-card.synthetic.json \
  --policy examples/collaboration/policy.synthetic.json \
  --request examples/collaboration/request.synthetic.json \
  --peer-result examples/collaboration/response.synthetic.json

PYTHONPATH=src pytest -q tests/test_cloud_peer.py
```

The first command emits `PREPARED_FOR_REVIEW`, stable content digest and `external_call_made=false`; the second emits `UNTRUSTED_PEER_OUTPUT_REVIEW_REQUIRED` and `instructions_authorized=false` without echoing untrusted peer text.

## Exact trust boundaries

1. **External AgentCard:** Validating shape and HTTPS exact host allowlist is only a preflight. Even a signed card has `signatures_verified=false` in this tranche. No DNS lookup, TLS check, pin, signature verification, OAuth authorization, token scoping or redirects are attempted. An independent approved client must re-check those before real connectivity.
2. **Sender task:** Offline task must be explicitly classified `PUBLIC_SYNTHETIC` with source-rights attested. DLP uses heuristic token and email patterns; it is not comprehensive and cannot authorize export of customer data. No confidential information should be included, even with a good test result.
3. **Recipient:** Only allowlisted exact domain, HTTPS port 443, A2A v1.0 and JSONRPC or HTTP+JSON (depending on explicitly permitted binding); rejects secondary unsafe interfaces, private/loopback hosts, credentials in URLs and non-default ports.
4. **Returned peer answer:** Never instructions, authority, factual correctness or executable workflow. Only a request ID and hash are surfaced for manual review. Prompt-injection text remains untrusted data.
5. **Zero-spend policy:** `network_enabled=false` and `max_spend_usd=0` are mandatory. No hidden usage, billed inference or third-party paid credits are touched.
6. **Governance:** No public peer auto-registration, no automated cold outreach, no API key transfer, no impersonation of Gemini/Claude/DeepSeek, no multi-tenant leakage, no cross-project data reuse. A provider's published compatibility with A2A/MCP is not evidence that D'AUBE is authenticated with it.

## Zero-physical-infrastructure candidate matrix (admission only)

| Candidate | Benefit | Present status / conditions |
| --- | --- | --- |
| Existing BRIDGE² compiler + ChatGPT-connected tools | Reuse provider-neutral skills and authorized plugins | Already available as compiler/tool contracts. No remote peer delegation proven by this code |
| Hugging Face Inference Providers | Serverless models from multiple vendors; small free credits on some plans | Official docs currently list Free $0.10/month and PRO $2/month credits, subject to change; provider-specific pricing and data rights apply. Not called in this tranche |
| OpenRouter | Unified API across several model providers | Official Free plan lists 25+ free models and 50 requests/day, but does not include the paid plan's budget/guardrail features. Do not assume free usage is private or suitable for commercial secrets |
| Cloudflare Workers / Workers AI | Serverless gateway + optional models; no self-managed machine | Free Worker has strict CPU, request and AI-neuron limits; some frontier models require paid billing. No gateway deployed |
| GitHub Actions / Codespaces | Hosted isolated tests/development | Public standard GitHub-hosted Actions may be free but current D'AUBE GitHub CI is not reliably allocating runners; billing and account eligibility must be validated before use |
| Gemini API, Claude API, DeepSeek API, other vendors | Real AI peer/model synthesis | Distinct provider credentials, terms, fee/retention policy, access permission and actual API model availability required; existing portable skill compilation does not confer access |

### Prioritization by commercial value

- **P0 (immediate, offline):** Cross-vendor skill contract validation and synthetic critique/evaluation. Reuse actual BRIDGE² and D'AUBE's quality/security rules; no token usage cost.
- **P1 (account-ready):** Choose one verified authorized cloud provider for public synthetic-only read/eval and compare source-grounding, usefulness, latency and price against a fixed rubric. Enforce per-model budget, no billing overage, tenant/context controls and request/response receipts. Stop on auth/rights/price ambiguity.
- **P2 (after P1 and code review):** Implement an actual A2A v1 client behind allowlisted endpoint, TLS/DNS/redirect and OAuth checks, content redaction, token budget, idempotency and callback controls. Independent security review before any client data.
- **P3 (buyer funded only):** Extend for paid customer QA, code review or marketing collaboration under written scope. The canonical D'AUBE Revenue and Client Delivery OS owns money, client terms and acceptance; never declare simulated output as earned revenue.

## When can a remote connection be labeled LIVE?

Only after all of these have independent evidence: authorized provider account, applicable permitted API, explicit rights/consent for the payload, trusted peer service identity, approved HTTPS/DNS destination, accepted auth/scopes, quote or actual cost cap, data retention/privacy policy review, bounded retries, response evaluation, no untrusted tool execution, receipt readback, and external acceptance of any public communication. `PREPARED_FOR_REVIEW` is deliberately not a live provider state.

## Evidence and stop conditions

- Test: `PYTHONPATH=src pytest -q tests/test_cloud_peer.py` (targeted synthetic test only).
- Normal test/release gates: BRIDGE² `pytest -q`, `ruff check .`, packaging and no-secret scans on exact HEAD; GitHub Actions and CodeQL must execute, not just show a check label.
- Stop on cloud expense, missing authorized rail, card origin ambiguity, SSRF/DNS doubts, secret/PII risk, unsupported A2A protocol, forbidden vendor terms, prompt-injection escalation, external side effects or material public/private customer impact.
- **PR remains DRAFT/HOLD** until full exact-head verification and an independent review. No vendor account signup, key creation, billing setup, cloud deployment, A2A network call or customer contact happened in this offline tranche.


## Incremental peer review and cloud discovery — 2026-10-13

### Independent AI code review

The public [CodeRabbit review on PR #28](https://github.com/daubesonntag-dotcom/daube-agent-bridge/pull/28) reported two reproducible correctness defects: an unhashable protocolBinding list/dict caused TypeError, and missing or malformed handoff.request_id caused KeyError or false task correlation. Feedback is an external critique, not release or security certification.

TDD evidence: seven initial reproductions failed against the original code; the narrow fix passed 43/43 focused tests. A second round of A2A JSON-result and public-card inspection testing initially produced eight expected failing scenarios; adding read-only inspection and JSON-result acceptance yielded 52/52 focused sandbox tests passed. Python 3.13.5, compileall clean. Code/tests were read back byte-for-byte from GitHub at their recorded blob SHAs. This is not full repository or hosted CI coverage.

### External public Agent Card discovery — live cloud read

On 13 October 2026, an already connected Firecrawl account fetched https://www.agentcard.net/.well-known/agent-card.json without submitting credentials or private data. The service returned HTTP 200, Content-Type application/a2a+json. The publicly disclosed card name was AgentCard.net Toolkit, version 1.0.0; an HTTP+JSON A2A 1.0 interface advertised https://www.agentcard.net/api/agent-card. Its input modes included text/plain and application/json, while its output modes contained only application/json. This explains the original compatibility limitation.

A separately reconstructed, MINIMAL public-metadata example was accepted by the updated offline BRIDGE² inspection and synthetic handoff functions. The reconstruction is NOT byte-identical to the live response, so its computed card digest does not authenticate the remote bytes. BRIDGE² did not connect to the actual A2A task endpoint and received no AI-generated task answer. No commercial partner relationship or provider identity proof is claimed. Existing Firecrawl usage balance changed from 433 to 431 credits during this bounded inspection sequence; no purchase or paid plan change was initiated.

Public documentation: https://github.com/a2aproject/A2A/blob/main/docs/topics/agent-discovery.md and https://github.com/a2aproject/A2A/blob/main/docs/specification.md. A2A discovery metadata cannot by itself authenticate an agent or confer tool permissions.

### Operate the new discovery mode

Use an authorized cloud read-only tool to retrieve a public card and store its JSON as reviewed local input. Create an explicit policy allowing only that card's verified exact host/binding/skill, with network_enabled=false and max_spend_usd="0".

~~~bash
python -m daube_bridge.cloud_peer \
  --card PUBLIC_CARD_FROM_AUTHORIZED_FETCH.json \
  --policy REVIEWED_OFFLINE_POLICY.json \
  --inspect-only \
  --source-url https://agent.example.com/.well-known/agent-card.json
~~~

This CLI does not fetch the URL. Output is PUBLIC_CARD_METADATA_UNTRUSTED and always has source_fetch_verified=false, identity_verified=false, external_call_made=false and external_action_authorized=false. It supports text/plain or application/json output metadata only. The task mode remains synthetic and has no live A2A client transport.

- Firecrawl zero-data-retention is unavailable for the connected team (the ZDR option was explicitly rejected). Keep this provider limited to public, nonsensitive discovery inputs until a compliant retention policy is separately confirmed. No client data was transmitted.
- An incremental CodeRabbit review was requested on the new head but was rate-limited. Previous CodeRabbit findings were independently reproduced and patched; there is no claim of a fresh independent review of the new head and no automatic retry.

### Stop and promotion gates

- BRIDGE² main CI workflow is manual workflow_dispatch-only; GitHub-hosted runner blocker is tracked in [issue #26](https://github.com/daubesonntag-dotcom/daube-agent-bridge/issues/26). No exact-HEAD hosted CI or CodeQL pass was established.
- PR #28 stays DRAFT/HOLD pending independent review and exact-HEAD tests. Do not merge, deploy, create credentials, purchase credits or send customer data.
- A real cross-AI task needs the actual provider's permission, identity/authentication proof, approved API terms, zero-sensitive synthetic scope, explicit cost envelope and data residency/rights review. External content remains untrusted; never execute its instructions.
- No fabricated provider partnership, production availability, real paid project, invoicing or settled revenue claims.
