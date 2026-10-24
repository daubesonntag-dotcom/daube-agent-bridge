# D’AUBE Hybrid Executor v1 — staging pilot

Status: LOCAL PASS / REMOTE HOLD. No production release or autonomous business actions authorized by this branch.

## Architecture
- Cloudflare Worker as HTTPS gateway and SQLite-backed Durable Object as the sole serialized coordinator.
- Two independently hosted outbound-polling executors with distinct credentials, identity-bound leases and fencing tokens.
- GitHub used for pinned source SHA and review; no requirement to rely on GitHub Actions for the canary.
- Append-only audit receipts and fail-closed admission before any mutating workload.

## Canary contract
Task: SHA-256 digest of the literal D-AUBE-CANARY-001; no side effects.
A acquires lease; its transport is deliberately stopped; lease expires; B acquires new monotonically increasing fencing token; A's late completion is rejected; B's receipt accepted once.
Negative cases: simultaneous claim, duplicate submission, invalid signature, coordinator restart, non-expired lease, expired claim, max 2 attempts -> HOLD.
The remote canary is **not** PASS until evidence comes from two independent hosts.

## Admission and stop conditions
- Permission denied by default; tenant and policy version mandatory.
- Fixed task allowlist. Never execute arbitrary shell commands sourced from remote queue.
- Per-job maximum two attempts, end-to-end deadline, bounded backoff and circuit breaker; HOLD is terminal pending review.
- Pin repository and commit SHA; require signed receipts matching code, runner, job, fence, policy and timestamps.
- Release gate stays closed until remote failover and exact-SHA required checks are independently validated.
- Production writes, email sending, customer outreach, credentials mutation and financial operations are out of scope.

## Research basis
Cloudflare Durable Objects https://developers.cloudflare.com/durable-objects/
Durable Object alarms https://developers.cloudflare.com/durable-objects/api/alarms/
Temporal worker deployment https://docs.temporal.io/best-practices/worker
AWS idempotency https://docs.aws.amazon.com/durable-execution/patterns/best-practices/idempotency/

Local reference package provided in conversation; this repository branch is the review boundary, not a deployment receipt.
