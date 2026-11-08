# Remote B reciprocal validation integration (local source only)

Base: daubesonntag-dotcom/daube-business-os-v2 PR101 HEAD177b69cb3dbc89b7f07c80a1feb3b745add64edb. Fetched handler blob ec9e402bc887d66f2db9c583070535eba059d539 and test blob04286a000d491675595363e77990b43f1cabdff8 through the GitHub read connector. The initial attempt to resolve this ref in daube-compute-mesh returned404; the parent supplied the correct verified repository before fetching. No denied action was retried or rerouted.

Candidate handler changes:
- Imports exact reviewed reciprocal.mjs (SHA2569e26143b6e77d1b0b629fa652a5aeddff4d798549614816b5442ed2751312bb1). The imported module bytes are unchanged.
- Uses checkChallenge with explicit request-selected sourceId and actual authenticatedActor from Office GET. Requires exact canonical CHALLENGE + mission, source actor agent:ti, tenantdaube, roomcouncil and UUIDs.
- Uses the same checkAck for prior ACKs, new POST receipts and cold read evidence. ACK is exactly `ACK <server UUID>` rather than prior incompatible colon format. Cold read revalidates both the source challenge and ACK; missing/contradictory evidence returns UNKNOWN_COMMIT, never success.
- Preserves existing route/method/body/Origin/Founder-verified-principal restrictions. Verified human email is NOT an act-as-B grant. New authorize(principal,scope) callback defaults to denial before any secret read. It must return a trusted grant matching actor agent:daube, exact mission, sourceMessageId, fixed destination and operation messenger.read (GET) or messenger.ack (POST including read/write/readback). It must implement actual permission, expiry, revocation and replay policy; none is invented here. The callback is a trusted integration dependency, never caller JSON or an unsigned header.
- GET bound now256KiB to match original bridge/client; POST receipts remain16KiB. Credential getter, response redaction, redirects forbidden, request512-byte bound and UNKNOWN_COMMIT/no-auto-retry semantics preserved.

## Packaging and owner integration

Proposed handler target: deploy/council-autonomy/remote-b-consumer-v1.mjs. Place reciprocal.mjs beside it, so the relative ES module import resolves. Existing owner must either bundle this module into the approved existing Remote entrypoint or include it as an explicit ES module in the same Worker version upload. Uploading only the handler source is insufficient. This artifact adds no public handler, binding, Worker, scheduler or deploy configuration. The existing root must supply verifiedPrincipal from verified JWT and a separately approved authorize implementation. Without it the candidate deliberately stays denied.

The Python file in  is a QA-only exact copy from daube-agent-bridge ref7b4ed58f, blobf8d24bf408cad7386966744943781ea6725f4f9d. Do not bundle it into a Worker. Node integration.test.mjs invokes its real Client.verify_reply and mocks only provider _call; this verifies canonical ACK-space interoperability, not real authentication or Internet operation. This review folder is integrations/ti-messenger/worker-custody-candidate/remote-b-integration/ in PR36; the original owner applies the integration to PR101.

## Migration and evidence boundaries

Canonical challenge text is a proposed opt-in format. Existing freeform mission-containing challenges and ACK:<id> messages will not satisfy the new contract. Both peers must adopt the format for new messages; do not silently rewrite old history or claim deployment compatibility. Deterministic B clientMessageId remains the source serverUUID; per-sender idempotency allows equality with A's clientMessageId.

This integrates the B handler code, not a running A/B service. A-side source generation uses canonical formatter; Python A-side verification was exercised only on mocked persisted provider data. B never claims reciprocalAReadVerified from its own write/readback. Pure helper input evidence still requires trusted authenticated transport. No durable ledger/freshness enforcement is added.

Run: node --test
Results:32/32 supplied tests pass. Test suites include9 migrated original tests and23 integration tests. No red-first claim for this integration. Independent review completed separately: 11/11 tests passed. Syntax and helper-byte equality checks are included in local evidence.

No PR101 writes, deployment, secret read, credential binding, account creation, policy grant, spend or new runtime performed. Full repository governance npm checks were not run because this is a scoped source snapshot, not a full checkout. Original single writer must run repository/full Worker gates before production integration or deployment. Source approval does not authorize persistent access configuration.
