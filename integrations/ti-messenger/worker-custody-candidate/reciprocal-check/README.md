# Opt-in reciprocal mission validation

Source-only pure helpers for the PR36 candidate lineage (requested base 7b4ed58f). Existing consumer.status and consumer.send are untouched; this standalone directory is not imported by either. No deployment, authentication, secret access, handler, ledger, scheduling or external communication occurs.

## Proposed wire format, not an existing protocol assertion

Challenge text is exactly `CHALLENGE 2fa20aca-bf79-5aa8-9cad-0a22d971ff34`, with kind `challenge`. No prefix, suffix, whitespace variation or substring match is accepted. ACK text is exactly `ACK <challenge server id>` with kind `text`. IDs must be 36-character UUIDs with versions 1–8 and variant 8/9/a/b. UUID case is accepted but preserved; ACK reference and client correlation are byte-exact. Mission text is lowercase and exact.

This is a NEW opt-in canonical challenge format. Existing challenges using another format will be rejected; do not silently apply this to production or rewrite historical messages. Both peers must explicitly adopt the same format before generating new challenges. The existing consumer still has its broader receipt-ID validation; this helper intentionally has the stricter mission contract requested and must not be presented as proof of compatibility with every historic receipt.

## Own check then cross check

For consumer B, observedActor must be agent:daube and the persisted challenge must be from agent:ti. For consumer A, observedActor must be agent:ti and the persisted challenge must be from agent:daube. Both additionally require expectedSourceId from the trusted caller selecting the intended challenge; it must exactly match the supplied challenge server ID. Do not derive it from an untrusted response merely to pass the check. Both require council room, daube tenant, exact canonical mission, challenge kind, and strict server/client UUIDs. Never infer observedActor from configuration: the integration must supply it from the verified authenticatedActor GET response. A pure function cannot authenticate its arguments.

Only checkChallenge success produces the proposed ACK text. It does not send it or authorize a write. The integration must separately acquire messenger.send authorization through the existing consumer. The ACK is accepted only after checkAck receives actual persisted evidence from the server, plus the expected ACK clientMessageId from the authorized send attempt or a trusted existing record. A new write receipt and a cold/prior ACK run the SAME checkAck path. It checks actor, room, tenant, text, kind, strict IDs and client-ID correlation, and rejects reusing the challenge server ID, including case variations. Client IDs are per-sender: opposite actors may use the same UUID. The expected ACK clientMessageId remains a trusted, exact correlation requirement.

Never synthesize an ACK object and claim success. Helper success means supplied evidence matches the contract, not authenticated provenance, delivery, recipient read, exactly-once execution or cryptographic verification. Missing trusted correlation for a cold ACK is unresolved, not permission to trust its own clientMessageId. There is no persistent deduplication or replay ledger; a previously seen valid ACK can still validate. The caller must supply trusted evidence and independently manage freshness and replay policy.

Test command: node --test reciprocal.test.mjs. All fixtures are synthetic. Tests exercise both A/B directions, strict mission grammar, identity failures, shared prior/new ACK failures, UUIDs and exact source linkage. Tests were created with the implementation; no red-first claim is made. No real A/B session or roundtrip has been verified.
