# Council dispatcher to Observer Messenger A: LOCAL SOURCE ONLY

Not deployed; no authorization, bindings, credentials or access changed. No ambient credential lookup. Existing Observer OwnerACK binding is NOT authorized for Messenger reuse.

Dispatcher caller is 36e8f959f2496da9255a16c830571eb7.access, never agent:ti. Actor A is established by the A credential mapping and Office response, not by Council claims. The copied A counterpart changes only its caller gate to the dispatcher; reciprocal challenge/ACK verification remains unchanged. Generic consumer and reciprocal modules are exact reviewed copies.

## Proposed wiring, not an installed route

Existing local root snapshot observer-machine.mjs exports SEC04ProbeOnly extends WorkerEntrypoint, currently only ownerAck334 and sec04KeySelfTest. rpc-methods.mjs provides a composition seam preserving a supplied base's methods, adding messengerAStatus, messengerARead, messengerASendChallenge, messengerAAck. No source rewrite or guessed root version performed. Owner must integrate into the current serving SEC04ProbeOnly, preserve original methods and bundle every import.

Council's approved entrypoint must forward the ORIGINAL raw signed Cf-Access-Jwt-Assertion in input.proof over the existing approved service binding. A decoded principal, client ID header or caller-supplied actor is insufficient. Observer proof-verifier.mjs independently verifies RS256 signature using fixed team JWKS, registered dispatcher common_name, machine app/empty sub/no email, expiry, issuer and Council audience. Inject the verifier into rpc-adapter; missing verifier, issuer/audience, authorization callback or credential provider denies. fetchCerts is required; there is no ambient network fallback. Parent provider read confirmed organization auth_domain jolly-mode-075c.cloudflareaccess.com and Council app audience 3ae2b154dac34ab91f643fcb55512f138a1fdc1bd31294837a6ce64d66f18739. The existing Remote root independently uses the same team issuer; no Observer audience is invented.

The raw bearer JWT does NOT cryptographically bind mission, operation or body. Each method independently requires an explicitly approved scoped authorize callback for exact dispatcher→agent:ti, mission 2fa20aca-bf79-5aa8-9cad-0a22d971ff34, tenant daube, room council, fixed Office endpoint and operation (messenger.status/read/sendChallenge/ack). Read, sendChallenge and ack additionally require sourceMessageId UUID (sendChallenge uses this as the outgoing clientMessageId). No callback is supplied by default, so there is no default grant. Callback fixture returning a scope is test-only. Access non_identity membership alone is not delegation.

Inputs contain only proof, missionId and (except status) sourceMessageId. Send text is generated canonical CHALLENGE + mission, ACK canonical ACK + validated peer server UUID; no arbitrary text/actor/destination. Read and ACK validate opposite B challenge plus prior/new/cold ACK evidence. Office must report agent:ti on GET and correct A sender on receipt. Stored/readback never claims peer receipt. POST uncertainty is UNKNOWN_COMMIT with safeToRetry:false. No automatic retries, nonce ledger, atomic grant/action admission or durable wake loop implemented. Repeated bearer invocation remains possible within approved scope; original per-sender clientMessageId semantics do not prove single execution or end-to-end replay protection.

## Missing runtime inputs

Exact current Council route/module source and service-binding target, current Observer root/module assembly, real running dispatcher client and credential custodian, owner-approved authorize implementation/TTL/revocation semantics, explicitly approved A credential getter/binding, approval of rollout/security changes. None inferred from account inventory. This source is not deployable until those are resolved. No new Worker/scheduler or production policy engine.

## Tests

node --test rpc.test.mjs uses synthetic RSA key/JWT, mock JWKS, synthetic credentials and fake Office. No real network/secret/DB operations. Independent source review passed 24/24 (21 supplied plus 3 independent) on rpc-adapter c84d3cb0. One subsequent disabled-composition test brings the local supplied suite to 22/22; source unchanged. Assembly patch applied cleanly to its exact historical base and node --check passed.

Dispatch-time expiry guard applies before every Office request, including after credential awaits and before cold read. Reused consumer conservatively reports UNKNOWN_COMMIT for send expiry detected in transport wrapper even if wrapper blocked the physical fetch; this does not authorize a retry. No claim of transactional grant freshness.
