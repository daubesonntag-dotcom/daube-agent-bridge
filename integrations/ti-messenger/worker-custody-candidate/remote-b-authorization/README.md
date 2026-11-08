# Local B authorization evaluator, not grant issuer

Executable factory createAuthorizeRemoteB({readCurrentGrant,now}) returns an authorizeRemoteB(principal,scope) callback compatible with the reviewed strict B handler. Missing reader, lookup exceptions or invalid results return null. No store, API endpoint, credential, environment flag, policy default or granted role is created. Current Access service-token membership in Remote/Office policies is authentication admission, not permission for this operation.

The principal must be the actual trusted existing Remote machine-JWT verifier result for B: exact verification marker/clientID/issuer/audience, unexpired numeric expiry, nonempty verifiedAssertion and no human email. The evaluator does not verify JWT signatures itself. The caller must not construct this argument from request body or unsigned headers. Neither Founder nor A/staff IDs receive authority here.

The handler scope must have exactly actor, missionId, sourceMessageId, operation and destination. Mission is pinned2fa20aca-bf79-5aa8-9cad-0a22d971ff34; source is strict UUID; actor agent:daube; operations messenger.read or messenger.ack; exact Office Council messages URL. Reader query adds subjectClientId, room council and tenant daube. It receives no raw JWT or credential. Selected primitive scope is copied before awaiting the reader.

## Proposed input contract, not an observed production schema

The injected readCurrentGrant must return a current authoritative snapshot:
- grant: exact requested subjectClientId/actor/missionId/sourceMessageId/operation/destination/room/tenantId plus notBeforeMs, expiresAtMs, revoked, version and fence.
- currentVersion and currentFence: current authoritative revision values from that same trusted lookup.

This local candidate requires both version and fence as nonempty bounded revision strings. This is an opt-in explicit contract, not a claim that a production store already supplies them. Missing version/fence, old mismatch or omitted revoked state denies. No values are synthesized. The owner must identify actual semantics and either provide an authorized adapter with equivalent checks or review a deliberate schema change. Do not invent versions/fences merely to pass.

Time is checked before and after lookup; JWT/grant expiry at the decision time fails closed. Explicit revoked:false is mandatory. All requested scope fields must match the grant exactly. Success returns only the original fixed handler scope, never grant contents/JWT/error data.

## Exact remaining inputs

1. Owner-approved trusted current-grant/revocation reader implementation and its existing authorized backend, identity and consistency semantics.
2. A real owner-approved B grant for the exact mission, source UUID and operation, including validity interval, explicit revocation state and meaningful revision/fence values.
3. Existing caller wiring passing only cryptographically verified Remote B identity, and approved packaging into the existing runtime. This file exports a factory; it does not create a production instance.
4. Independent runtime verification and any required action-time approval for persistent access/security changes.

## Limits and risks

A hash or a function name cannot prove the reader is authoritative or current. Fabricating a snapshot bypasses the intended trust boundary; matching version/fence fields inside a stale snapshot cannot establish freshness independently. The reader must retrieve current policy/revocation, not merely echo request values or cached Access membership. This evaluator does not issue/refresh grants, consume a nonce, maintain replay state, serialize actions, enforce one-use permissions or resolve revocation between decision and subsequent operation. Revocation/action race and exactly-once behavior remain unresolved integration requirements. Do not claim nonce/generation/replay safety from this source.

32/32 isolated tests pass with explicitly synthetic fixtures. Tests include missing source, malformed/membership-only data, wrong identity/scope, expired/revoked grants, version/fence mismatch, scope mutation, lookup failures and expiry during lookup. Tests were written alongside implementation, not claimed red-first. No live policy lookup, grant issuance, secret access, external writes, publication or deployment occurred.
