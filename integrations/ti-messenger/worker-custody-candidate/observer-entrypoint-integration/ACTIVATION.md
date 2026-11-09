# Concrete wiring candidate: disabled source only

The assembled Observer root and published RPC/verifier modules are unchanged. The historical v25 provider-downloaded multipart snapshot matches the root SHA256 5cfb33d86601641a724cd964267fe8a5a8c062c4e405437555e1cee59cacb49b and original OwnerACK transport modulo MIME framing newline; contemporaneous release records support historical provenance, not a fresh serving-version byte match. Only messenger-runtime-config.mjs is replaced with a concrete dependency builder; wiring.test.mjs is added. No new policy engine, Worker, scheduler, store, signer, token or public route. This is a proposed compiled delegation, not an authorization already issued.

## What the module does

Production messengerDependencies(entrypoint) always selects the immutable COMPILED_POLICY in source. It does not accept env/body policy input. The published policy remains enabled:false, revoked:true, revision:UNAPPROVED, zero time bounds, empty source IDs. Invalid/inactive policy returns empty dependencies before environment, credential or network access. Test dependency injection is not connected to an RPC method.

An approved active policy supplies the actual RS256 dispatcher verifier with pinned Council audience/team issuer, an exact scope authorizer, a lazy getter for the existing TI_MESSENGER_CREDENTIAL Secrets Store binding, and destination-constrained Office/JWKS fetch. The getter is invoked only after JWT and scoped authorization by the existing RPC adapter. Existing OwnerACK-only binding approval does not authorize Messenger use. This package does not read the binding.

Fixed grant: dispatcher 36e8f959f2496da9255a16c830571eb7.access → agent:ti; tenant daube, room council, mission 2fa20aca-bf79-5aa8-9cad-0a22d971ff34; exact Office council-messages endpoint; messenger.status/read/sendChallenge/ack only. Non-status operations additionally require one of at most eight explicitly approved source UUIDs. Challenge send uses that UUID as clientMessageId. The authorizer validates exact scope fields, not a matching subset. B receives no authority from this grant.

Policy lifetime uses absolute Unix milliseconds, positive and at most 900000 ms (15 minutes). It is never renewed from invocation time. Validity is checked before dependencies are exposed, authorization, credential lookup, after lookup, and before every physical network request. Once a dependency instance observes expiration, invalid clock or backward clock, it stays denied. This latch is per dependency instance only: existing RPC composition constructs dependencies per call, so it does not establish process-wide clock-rollback protection or authoritative time across restarts. Changing the original policy object does not mutate a captured decision. Production config is compiled, not externally writable.

## Exact activation edit, pending approval

Only after the owner approves the full tuple below, replace the one COMPILED_POLICY literal in messenger-runtime-config.mjs with: enabled:true; revoked:false; revision:<approved unique revision>; notBeforeMs:<approved absolute start>; expiresAtMs:<approved absolute end within 15 minutes>; sourceMessageIds:<approved exact UUID list>. Keep every fixed actor/destination/scope restriction unchanged. Do not fill placeholders with guesses, use Date.now() to roll the TTL, or make environment flags an enable path. No activation values have been selected in this candidate.

This activates the existing assembly only when that module is included in the owner-reviewed deployed bundle AND the separate runtime/binding approval is satisfied. It is not a deploy instruction or evidence the Council caller exists. The existing complete-root candidate still requires authoritative active-source comparison; current Council wiring and actual dispatcher custody remain missing.

## Required per-action approval tuple

- Target: existing daube-edge-observer-v1, SEC04ProbeOnly; exact reviewed active-baseline version, full candidate module hashes and rollout target (not yet finalized).
- Caller: the existing dispatcher client above, through owner-confirmed Council route/service binding; original signed Council JWT independently verified at Observer. Actual running caller and secure custodian remain unresolved.
- Privilege/data change: permit these four mission-scoped Messenger operations as A, and permit the existing TI_MESSENGER_CREDENTIAL binding's A credential to be used only toward Office for that purpose. No secret is returned or exported; no new credential or binding is created by this code.
- Scope/time: exact UUID list, revision and absolute start/end to be supplied and approved. Maximum 15-minute delegation; no implicit renewal. Repeated operations with approved IDs remain possible.
- Risk: a compromised approved dispatcher may exercise those operations within the scope/window. Access JWT is a bearer, not a body signature. No nonce ledger, one-shot budget, or transactional revocation-to-action proof.
- Revocation/rollback: owner-approved replacement disabling the compiled policy and rollback to an identified baseline; do not roll back unrelated bindings. Determine serving-version rollout/propagation before claiming immediate revocation. In-flight requests may commit; old serving copies retain their bounded original TTL. Token/key rotation and revocation require separate approved credential actions and custodian execution.

Do not proceed with activation while tuple fields are unknown or approval is absent. Read-only reconciliation and independent source tests may continue.

## Recovery and evidence

JWT/policy expiration denies new physical requests. Obtain a new legitimate session or a newly approved bounded policy; do not switch to Founder or another machine. Revocation is compiled-source/rollout plus the existing Access enforcement semantics, not an invented live revocation service. A durable shared revocation source is necessary only if the required latency cannot be met with the approved bounded policy.

POST uncertainty stays UNKNOWN_COMMIT/no automatic retry, including conservative reused-consumer classification when a transport guard blocks dispatch. Reconcile matching sender/clientMessageId and server receipt before retry decisions. Four distinct A-challenge/B-ACK/B-challenge/A-ACK IDs plus independently authenticated peer reads remain necessary for live reciprocal proof. None are produced by these synthetic tests.

## Local validation

node --test *.test.mjs: 60/60 supplied tests pass. Includes original assembled-root and OwnerACK regressions, real synthetic RSA/JWKS proofs, all four synthetic activated operations, inactive/revoked/expired/overlong policy, exact scope/UUID rejection and expiry during secret lookup. No external network, real secret access or production changes. Independent bounded review passed 63/63 (60 supplied plus 3 independent), including the reproduced expiry-to-backward-clock regression after remediation. This does not approve activation or establish live runtime evidence.
