# Messenger outbox: offline review candidate

**SOURCE ONLY. Not installed, registered, deployed, scheduled, or network tested.**

This standard-library Python/POSIX module adds a local persistent queue, not an
Autopilot service. No changes were made to the credential-FD candidate or original
Messenger client. There are no credentials, live endpoints, network calls, or
production integration in this package. Fake transports exercise the contract.

## Safety contract

- The caller supplies stable operation and client message IDs. Both are globally
  unique in one database. Duplicate enqueue with the identical binding returns
  the existing operation; any differing principal, room, payload, ID or attempt
  bound is rejected. SQLite also prohibits updates to these binding columns.
- Attempts are persisted before transport invocation. `run_once` performs at most
  one attempt, with a stored bound of 1–10 attempts. It does not sleep or loop.
- SQLite commits use synchronous FULL. A POSIX advisory file lock covers the
  complete claim/send/finalize or reconcile cycle. A second cooperating process
  returns BUSY. This serializes all messages, intentionally trading throughput
  for simpler crash safety. A hung transport blocks progress; no lease expires
  and no time-based takeover risks a duplicate.
- Restart leaves claimed operations IN_FLIGHT until the next worker/reconcile
  obtains the exclusive lock, then holds them UNCERTAIN. A crash before actual
  transmission may therefore need reconciliation too. This is conservative.
- A transport exception, unknown/malformed result, missing binding, or malformed
  receipt is UNCERTAIN, never automatically retried. Exception text is not stored.
- A DENIED result is terminal. Reconciliation cannot revive DENIED, STORED, or
  EXHAUSTED operations. This component supplies no denial override; authorization
  changes need separate review and must not be disguised by making fresh IDs.
- Positive STORED evidence requires a nonempty receipt plus exact principal,
  room, client message ID, and SHA-256 of canonical payload. This means storage,
  not recipient delivery/read or a cryptographic receipt.
- Only a fully bound NOT_SENT verdict permits another attempt. It must positively
  establish that the attempt was never accepted and cannot be accepted later.
  Absence from recent-message history, an HTTP error, timeout, or a retry hint is
  insufficient. At the limit, NOT_SENT transitions to EXHAUSTED.

Transitions: QUEUED -> IN_FLIGHT -> STORED / DENIED / UNCERTAIN / QUEUED /
EXHAUSTED. UNCERTAIN -> STORED / DENIED / UNCERTAIN / QUEUED / EXHAUSTED only
through an explicit verifier. IN_FLIGHT -> UNCERTAIN on crash recovery.

## Trust and integration boundaries

The injected transport and reconciliation verifier are trusted application code.
Caller-provided principal strings and Result fields are **not identity proofs**.
A future authorized live adapter must independently authenticate the gateway and
principal, route to the exact room, send the exact persisted payload and same ID,
and validate server-backed full-binding evidence. Echoing the input into Result
is suitable only for these synthetic tests, never production verification.
The component does not create permission to send or expand existing approval.

`classify_legacy_response` is a fail-closed classifier, not a live adapter. It
marks authorization denials/missing identity/blocked login redirects terminal
and holds all other legacy responses for reconciliation. The existing client's
`safeToRetryWithSameId: true` is explicitly ignored. Its STORED_BY_SERVER receipt
lacks verified room/payload binding and cannot satisfy this contract on its own.
A READABLE status does not establish an authenticated expected principal.

The SQLite file stores principal, room, canonical text/kind payload, attempts,
state and receipt **in plaintext**. No credential/configuration fields are
supported or read. However, a user could embed a secret in text or a receipt:
this module cannot detect that. Callers must supply authorized nonsensitive
message payloads and nonsensitive receipt IDs. Private file permissions do not
equal encryption, secure erasure, or protection against the same OS account.

Use a private owned directory on one trusted local filesystem. Existing database
and lock must be private owned regular files; symlinks/FIFOs are rejected. Do not
use NFS/network filesystems, delete/replace the lock, modify SQLite externally,
or let untrusted same-UID processes mutate the directory. Multiple database
copies have no shared uniqueness guarantee. Losing/restoring stale storage can
lose deduplication history. This is a source candidate, not a security boundary
against hostile local processes; OS crash/power-loss durability depends on the
filesystem and storage hardware and has not been fault-injection tested.

## What is and is not proved

Local immutable enqueue deduplication and single active attempt are tested;
**local exactly-once bookkeeping is not network exactly-once delivery**. Crash
uncertainty is deliberately preserved. There is no verified remote idempotency,
credential custody, A/B principal enrollment, server receipt verifier, delivery
proof, service uptime, wakeup source, backoff schedule, or **24/7 guarantee**.

Future integration needs independent source review, authorized transport and
verifier implementations, live gateway/server-contract validation, and explicit
runtime/scheduling/credential approval where required. Do not bypass existing
source pins or retry denied operations using this candidate.

## Offline verification

From this directory:

    python3 -m unittest discover -s tests -v
    python3 -m py_compile outbox.py tests/test_outbox.py

Tests cover duplicate and conflicting enqueue, restart persistence, terminal
denial, legacy retry-hint rejection, uncertain reconciliation, invalid evidence,
maximum attempts including uncertain final attempt, exception non-disclosure,
actual spawned process death, two spawned competing workers and concurrent
reconciliation exclusion, binding SQL trigger, unsafe file types/permissions,
and rejection of credential fields. Results are recorded in test-results.log.
Tests use synthetic values and make no network calls. No production or complete
upstream repository gates are claimed.

## Explicit existing-client adapter (source only)

`messenger_adapter.py` now provides `MessengerTransport(client, surface)` for
explicit injection into `Outbox.run_once`. It calls the existing reviewed
`Client.send` exactly once, without a second HTTP implementation, polling,
credential lookup, registration, installation, scheduling, or automatic retries.
Construction does no I/O. This source is not wired into the MCP entry point or
installed by the installer. Its source-only addition is not deployment approval.

Before calling send, it requires a supported queued principal (`agent:ti` or
`agent:daube`), room `council`, and the same principal returned by the existing
client's strict configured-identity check. A different or unknown principal is
DENIED before HTTP. Noncanonical payloads are held rather than rewritten. The
adapter is deliberately limited to tenant `daube`, room `council`; other rooms or
tenants require a separately reviewed binding/schema, not configuration guesses.

The client now retains the validated persisted receipt's text and kind in its
STORED_BY_SERVER result. The adapter requires those returned values, not copies
of queued inputs, plus exact sender, tenant, room and clientMessageId, a valid
2xx status, and a nonempty bounded server messageId. It computes the digest from
returned persisted text/kind and compares it to the immutable queue digest.
Server message IDs remain opaque under the existing API contract; the supplied
clientMessageId (commonly a UUID) is matched exactly, never generated or changed.
Replay receipts pass the identical checks.

`adapt_send_result(message, response)` is a pure conversion helper, **not an
identity/authenticity verifier** for arbitrary dictionaries. Its input must come
directly from the reviewed Client.send instance for this authorized operation,
never from user/model-generated data, unrelated MCP results, or invented receipt
fields. Tests inject a fake opener only. Matching strings or hashes alone do not
prove gateway authentication, server persistence, or recipient read in live use.
The callable wrapper preserves the intended direct Client.send data flow, but
Python dependency injection is a trusted-code boundary, not a sandbox.

Legacy/incomplete/mismatched receipts remain UNKNOWN -> UNCERTAIN. Post-send
identity contradictions, 502s and timeouts remain UNCERTAIN even if the server
may already have stored the message. Existing known authorization denials stay
DENIED. The adapter never emits NOT_SENT and supplies no reconciliation verifier;
unknown operations still require independent authoritative reconciliation. Cold
read absence alone is never a retry authorization. No new transport, persistent
access, network validation, delivery proof, or 24/7 guarantee is claimed.

Additional offline adapter tests run with the same unittest discovery command.
They exercise both actors, replay, exact outgoing ID/payload, each missing or
mismatched receipt binding, malformed fields, unknown/mismatched principals
before HTTP, actor contradictions after POST, 401/403 versus 502/timeout,
and actual client -> adapter -> outbox transitions without duplicate attempts.
