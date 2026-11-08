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

Node24: 95 send tests, 23 status tests and 6 prior independent tests pass (124 total). Run `node --test consumer.test.mjs independent.test.mjs status.test.mjs`. Dependency-free original candidate code uses platform APIs and Node built-in test modules. Repository root MIT License applies; no third-party library or model is bundled. This directory is deliberately not imported by the installer or production entrypoints.

## UUID clientMessageId correction

The published candidate accepted arbitrary 12–90 character identifiers. This was incorrect for the bridge REST contract. This revision uses the bridge UUID pattern (versions 1–8, variants 8/9/a/b, case insensitive), with an additional exact 36-character length check to reject trailing line terminators. Invalid values fail before credential binding access or transport. Case is preserved for receipt correlation. Receipt message.id retains its existing string/alphanumeric contract; no evidence justified changing it.

Contract reference: bridge source blob 42414cbffdea111aae1f98d0b1bd80c9941d7721, supplied for this correction; publication baseline PR36 HEAD 7186f538c0161713b4e2d971f9b9068d57e26880. This is source-only contract QA, not live bridge validation.

Tests were updated first: all positive clientMessageId fixtures now use UUIDs. The new suite against the original consumer yielded 101 tests, 92 pass, 9 fail. After the code correction, all 101 pass. Coverage includes all 64 combinations of versions 1–8, variants 8/9/a/b and lower/upper case; malformed/non-string inputs; and prior scope, DTO, SSRF and ambiguous-commit negatives. No production call or deployment occurred.

## Source-only identity status probe

status(callerEvidence) requires a separate explicit messenger.read grant for the same fixed caller, actor and destination. A send grant is insufficient. Only then does it read the injected credential binding and perform GET to the exact fixed endpoint with redirects forbidden. There is no new caller verifier, public endpoint or runtime configuration.

The existing PR36 Client.status source contract is room=council, messages array and authenticatedActor exactly matching agent:ti or agent:daube. The probe returns observedActor from that server response only, along with count and canSendVerified=false. It never returns messages or raw errors. The GET response limit is 256 KiB, matching the original bridge/client contract. The POST receipt limit remains 16 KiB. Founder, missing actor, opposite actor and malformed contracts cannot establish identity. GET failures return READ_UNVERIFIED; no observed identity or automatic retry is produced. Existing send UNKNOWN_COMMIT semantics remain unchanged.

This probes authentication/readability only. It does not create an account, bypass login, grant anonymous access, prove send permission, prove recipient readback or establish continuous connection. Caller, binding and deployment approvals remain absent.

RED first: all 19 new status tests failed against the UUID-only base because status did not exist. GREEN: 124 tests pass, preserving all 101 existing tests. Source contract inspected in the installed PR36 validation/ti_messenger_mcp.py Client.status; integration against a deployed Worker remains unverified.

Independent review found the initial 16 KiB GET cap rejected valid busy-room responses. GET only now accepts up to 262144 bytes; tests cover a valid >16 KiB room, exact 262144/262145 boundaries and reader cancellation. POST limit is unchanged.
