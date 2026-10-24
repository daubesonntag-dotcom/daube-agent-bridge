# GCP A admission + Electron browser-control integration — staging only

Date: 2026-10-24. Release: HOLD.

## Source staged
- `hybrid-executor-v1/gcp/executor-a.py`: fixed canary job, host-native GCP signed identity token, bounded HTTP timeouts, never logs JWT; `start`, `state`, `claim-no-complete`, `stale-complete` modes.
- `hybrid-executor-v1/browser-control/browser-control.cjs`: owner-only Unix socket (`0600`), `GET /health`, `GET /inspect`, and URL-allowlisted `POST /navigate`; no public TCP listener, no arbitrary shell, no remote JS evaluation.
- Full local test package: prepared separately in conversation. **The repository's exact commit is not CI-verified**; do not equate local tests of a draft with a required check.

## Required host integration before use
The running Electron Main file on GCP is `/opt/daube/sovereign-browser/electron/main.cjs` (root-owned application tree). Create a reviewed patch in the canonical source repository, then use the authorized deployment pipeline. Add:
```js
const { startControlSocket } = require('./browser-control.cjs');
```
After `await createMainWindow()` in `app.whenReady()` start the socket with `activeTab` and a callback that navigates via `tab.view.webContents.loadURL(url)`. End navigation with `tab.view.webContents.getURL()`.

Do not install by using SentinelX scripting/exec to bypass the read-only file policy on `/opt`. The current agent policy has `/opt` `access:r` and no `writable_paths`. Current Desktop Commander tool usage is exhausted. Operator-approved narrowly scoped deploy permission or a separate already-authorized release runner is required.

## Real failover acceptance — all must PASS
1. Pin coordinator / B Worker sources and a **new** fixed job ID `CANARY-20261024-FAILOVER-02`.
2. VM A obtains signed Google instance token locally. Cloudflare verifies Google RS256 signature, audience, expiry, expected service account and VM ID.
3. A creates and claims job (fence=1); ensure B is not allowed to acquire a live lease.
4. Stop A or deliberately refrain from completing. After its lease expires, B's scheduled trigger claims with fence=2 and computes SHA-256.
5. A stale completion (fence=1) returns HTTP 409; B completion accepted exactly once; no third claim.
6. Read back Durable Object SQL receipts + exact source SHA and independent host job logs, disable Cron.
7. CABINET admission policy and exact-commit release required checks remain separate mandatory gates.

Existing **B-only** remote canary `CANARY-20261024` passed on Cloudflare. This is not evidence of A→B failover.

## Reference manuals
- https://docs.cloud.google.com/compute/docs/instances/verifying-instance-identity
- https://developers.cloudflare.com/workers/wrangler/configuration/
- https://developers.cloudflare.com/workers/runtime-apis/bindings/service-bindings/
- https://www.electronjs.org/docs/latest/api/web-contents
- https://www.electronjs.org/docs/latest/tutorial/security
