# Source-only Workers custody design

Status: local integration seam and synthetic Node tests only. No Worker selected, deployed, configured, or invoked. No credentials accessed. No public handler or token-return endpoint. No new Worker, scheduler, wake loop, or network workaround.

## Proposed boundary

An approved existing Worker authenticates the caller and verifies an explicit scoped grant: caller, agent actor, messenger.send operation, fixed destination. Identity alone, including Founder identity, is insufficient. Instantiate separate factories/configuration for A and B; never select a credential using the request body. The injected verifier is deliberately unimplemented and must not trust unsigned body/header claims.

Only after authorization and input validation does the factory call an injected Secrets Store binding's get(). The secret remains within Workers memory and the outgoing request to the fixed approved Messenger endpoint. There is no route to return it to local Ti. Headers, raw errors and upstream bodies must not be logged by the integrating Worker. Review traces for redaction before enabling production observability.

A/B credential sources are Workers-scoped. Neither a new runtime nor binding is approved by this candidate. The existing Observer OwnerACK-only binding must not be reused. Council as B host is a proposal, not approval. No store IDs or secret payloads are included.

The fixed client-ID/actor mapping uses the existing source contract. Public client IDs are identifiers, not secret values. Actual secret JSON has NOT been inspected. The local FD client's contract is clientId/clientSecret. This candidate deliberately accepts only a flat two-field JSON serialization in that order, no escaping or duplicate keys; another safe stored serialization may be rejected. Custodian must confirm shape without exposing values before integration; do not rewrite or rotate a secret to satisfy this prototype.

## Runtime contract and limitations

Source contract: existing integrations/ti-messenger/ti_messenger_mcp.py at PR36 commit 9e0cbef supplies REST message fields and receipt expectations. Credential JSON field names are a prototype contract assumption, not a verified stored payload. No claim these establish live Worker payload shape.

The caller supplies only text, kind and idempotency clientMessageId. Actor, room (council), tenant (daube) and destination are fixed. Redirects are forbidden. Incoming size, credential size and response streaming size are bounded. A matching receipt returns only a small sanitized persistence result, never recipient-read success. All post-dispatch failure/mismatch outcomes are UNKNOWN_COMMIT with safeToRetry=false. Readback/reconciliation is not implemented. No automatic retries, storage queue, cross-instance rate limiter or replay ledger is implemented. Integration must supply quotas and scoped grant lifetime/replay controls.

Node tests verify pure logic with synthetic credentials and mocked transport, not Cloudflare/workerd compatibility. No runtime target compatibility date, generated binding types, repository-wide gates, live auth, principal mapping or A/B roundtrip has been verified. Workerd integration validation must follow target selection.

## Required decisions before any binding/deployment

1. Exact existing A Worker name/environment and separately exact B Worker name/environment.
2. Authorized custodian and explicit authorization to bind each exact store entry to its target.
3. Exact authenticated caller, trusted verification mechanism and allowed actor/operation/destination grant, including expiry and replay/rate limits.
4. Exact destination and room; current candidate accepts Council/Office REST council room only, neither is selected as approved.
5. Action-time confirmation for persistent access configuration and any deployment that expands access. No configuration is included to accidentally perform this step.

A deployed on-demand consumer could be available across requests; that is not a continuously connected agent or autonomous wake loop. Persistent scheduling/replies are not implemented or enabled.

References: https://developers.cloudflare.com/secrets-store/integrations/workers/ documents binding configuration and required Super Administrator or Secrets Store Deployer role. https://developers.cloudflare.com/workers/runtime-apis/bindings/ documents request-context I/O. These document capability, not this user's authorization.

Run isolated tests: node --test consumer.test.mjs

## Source QA and license

Node24: 20 supplied tests plus 6 independent tests pass. Run `node --test consumer.test.mjs independent.test.mjs`. Dependency-free original candidate code uses platform APIs and Node built-in test modules. Repository root MIT License applies; no third-party library or model is bundled. This directory is deliberately not imported by the installer or production entrypoints.
