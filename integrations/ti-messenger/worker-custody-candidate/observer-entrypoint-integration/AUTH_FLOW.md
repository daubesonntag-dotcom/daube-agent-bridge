# Messenger authentication and rollout contract

## Source status

This is a complete source-only Observer assembly with Messenger disabled, not a deployment or live authentication result. It uses PR36 dependency commit 95b67ed0791f0da82b1e2b6f2951284a657006fe unchanged and the historically recorded Observer v25 root, SHA256 5cfb33d86601641a724cd964267fe8a5a8c062c4e405437555e1cee59cacb49b. Current serving bundle bytes are not independently matched to that root. Latest staged content is not proof of serving content and must not introduce a scheduled OwnerACK path. Existing public fetch, scheduled handler, Checker and OwnerACK logic are preserved byte-for-byte apart from the named entrypoint's base composition. No new schedule, Worker, store or binding.

## Identity lanes

- Founder: separate human identity-provider/OAuth sign-in through the existing human Access application and human-only routes. No email-to-agent conversion, shared Founder token or machine impersonation. Existing provider configuration, redirect/callback routes and scopes must be confirmed; this package implements no new OAuth flow. Human consent does not substitute for a machine runtime's scoped authorization.
- Dispatcher: existing client 36e8f959f2496da9255a16c830571eb7.access authenticates to Council's Access application. Council forwards the original signed assertion over the approved service binding to SEC04ProbeOnly. The Observer verifies the assertion again against issuer https://jolly-mode-075c.cloudflareaccess.com, fixed issuer JWKS, and Council audience 3ae2b154dac34ab91f643fcb55512f138a1fdc1bd31294837a6ce64d66f18739. Only signed app tokens with that exact common_name, empty subject and no email qualify. This establishes the dispatcher caller, not actor A.
- A: a separately approved scoped policy delegates the exact dispatcher operation to agent:ti. Only afterward may the approved A credential provider be read. Office must identify A through its authenticated response and receipt sender. The A client is 8ceae31b13c0a5f495c8374e6a8aced4.access; it is not the inbound dispatcher identity.
- B: independently authenticated B runtime/caller and its explicit scoped policy use B's own credential (6120a6eb353588180a8f8c8ca93a39a1.access), with Office observing agent:daube. This A package does not grant dispatcher→B, install B handlers or approve a delegated Founder path. B's exact approved runtime, ingress/verifier, strict machine-only source and authorization remain separate rollout inputs.

## Scope and session checks

All A methods fix tenant daube, room council, mission 2fa20aca-bf79-5aa8-9cad-0a22d971ff34 and the Office council-messages endpoint. Method names separate status, read, canonical challenge send and canonical ACK. Read/ACK require a selected source UUID; challenge send uses its selected UUID as clientMessageId. Scoped authorization must match caller, actor, operation, mission, tenant, room, destination and selected ID where applicable. Existing non_identity Access membership is authentication, not this delegation.

The signed bearer authenticates a principal, not the RPC body. No body signature, nonce budget or replay ledger is claimed. Signature/claims/expiry are verified before secret access; expiry is rechecked after asynchronous work and immediately before every physical Office request. No expired session fallback to Founder or another machine identity. Missing configuration denies without network or secret reads. messenger-runtime-config.mjs deliberately returns empty dependencies; no flag can enable it.

Owner-reviewed activation must replace that configuration with the pinned verifier, explicit authorize implementation, separately approved credential getter and fixed Office transport. Do not reuse OwnerACK-only credential authorization for Messenger. Fixed-scope policy may suffice if approved revocation semantics permit it; D1 is not automatically required. Policy reads alone do not prove atomic revocation-to-action admission.

## Expiration, recovery and revocation

Expired JWT: stop and obtain a new legitimate dispatcher session through its approved credential runtime. Do not persist assertions in logs or recover by copying another actor's secret. Revoked policy/caller: deny new operations through the authoritative enforcement layer. Existing JWT validity can outlast token or Access policy changes unless online revocation semantics are verified; effective revocation latency must be documented before activation. In-flight operations may already have committed.

Rotation is owner-controlled: identify the credential custodian and approved storage target, authorize the exact persistent-access change, update the original runtime through its secure secret mechanism, verify observed Office actor and negative cases, and revoke obsolete material under an approved recovery plan. This package performs none of these steps and creates no credentials.

## Idempotency and evidence

Reuse the selected clientMessageId only for reconciling the same intended message. Original idempotency is per sender, so A and B may legitimately use the same client UUID; server IDs still must differ. On POST timeout, malformed receipt or later readback failure, report UNKNOWN_COMMIT and do not automatically retry or generate a new ID. Independently read the matching source/receipt and reconcile first. Authorization expiration that blocks transport is conservatively classified as uncertain by the reused sender; it does not authorize retry.

Live two-way proof requires four distinct Office server IDs: A challenge, B ACK, independently originated B challenge, A ACK. Verify each observed actor, exact mission/canonical text, tenant, room, kind and client correlation. Consumer self-readback proves storage only. Separate authenticated peer reads are needed to claim the peer saw each corresponding message. Synthetic test IDs are not live evidence.

## Exact remaining rollout inputs

1. Authoritative active Observer bundle/version and preserved bindings, matched to the assembly baseline; do not substitute latest staged content.
2. Owner-supplied current Council source, exact route and service-binding target, plus actual running dispatcher client and secure credential custodian.
3. Explicit dispatcher→A policy, approved A binding use, TTL/revocation semantics, and independent B equivalents. No implicit authority from token names or access membership.
4. Reviewed assembled hashes, module inventory, exact activation/security approval, rollback version and post-rollout negative/identity tests. Default-deny source tests are not live success.
