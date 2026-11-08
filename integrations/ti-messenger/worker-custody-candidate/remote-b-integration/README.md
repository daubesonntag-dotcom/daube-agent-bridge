# Existing Remote B verified-machine caller adaptation (local only)

Source evidence: original Remote v8 root SHA25650cf4a887f3f406c3bfde3835f5026b2a4b1274911f0702242b12930ce55c23e, matching existing release manifest, implements authenticate(req,{machine:true}). It verifies RS256 signature via Access certs, issuer, audience, expiry, app type, empty subject, no email and registered client ID. Its actual return shape is verification:'ACCESS_JWT_RS256_VERIFIED', clientId, issuer, audience, expiresAtMs and verifiedAssertion. It does not return an actor or isMachine flag. The existing machine messages route already uses this branch.

Mismatch: prior B assembly placed the ACK route after authenticate(req) with default machine=false, which requires human email. The B handler then required an allowed Founder email. A genuine verified B service identity could not reach the intended handler.

Local adaptation:
- Handler accepts the actual trusted machine verifier shape for B client ID only, exact issuer/audience, fresh finite expiry, nonempty assertion and no email. A client ID, mixed context, missing marker and stale context fail before secret read.
- The handler does not itself verify signatures. Its second parameter MUST come directly from the original verified authenticate result, never raw request JSON/headers. Synthetic shape tests prove validation logic only, not cryptographic provenance.
- Verified B identity is still insufficient: explicit scoped authorize(principal,scope) must succeed before any credential access. Default authorization denies. No authorization module or grant is provided.
- Deliberate human delegation remains possible through the existing verified human path only with the same explicit scoped callback; email alone grants nothing.
- Root candidate uses authenticate(req,{machine:true}) for the exact B ACK path before the human gate, preserves POST Origin/content-type and sec-fetch-site checks, and passes its returned machine context to the B handler. An authenticated A machine reaches the handler and is rejected there. If machine authentication fails, the original human verifier path remains in place; it still requires its own valid authentication and scoped authorization.
- Existing machine verifier and other original routes are untouched. This is a local candidate security-sensitive route change, NOT permission to deploy it.

Files: worker.mjs is the adapted root; remote-b-consumer-v1.mjs is the adapted handler; reciprocal.mjs unchanged. Root imports remote-b-authorization.mjs, deliberately MISSING because no approved real authorize implementation exists. The unchanged Office bridge module and current complete original metadata/bindings must be supplied by owner before bundling. This package cannot yet be treated as executable production assembly. Python is an exact test-only fixture, not a second installed client.

Tests: node --test in this directory =>45/45 (13 new context/route tests plus32 prior integration regressions, including Python mock provider verification). Root syntax passes; no full signed-JWT root runtime/bundler test or real provider session was performed. No new persistent access, credential value, deployment, binding or external write occurred. Any live security/caller-path change and persistent integration remains subject to action-time approval and independent provider review.
