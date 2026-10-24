# GCP Electron browser-adapter staging evidence — 2026-10-24

Mode: **isolated staging**, no production app changes. Host: daube-host-01. Test source pinned to PR #30 SHA `880dcd8df8cddaafef7d9dd4946643ae276da96e`.

## Verified result
SentinelX authorized one-off temporary script ran as its non-root user on GCP, using a separate Xvfb display `:138` and temporary Electron profile. The helper `chrome-sandbox` remained root-owned mode 4755 and sandbox was **not** disabled. A temporary copy of `electron/main.cjs` imported `hybrid-executor-v1/browser-control/browser-control.cjs` from the exact SHA and started its Unix socket after `app.whenReady`, before `await createMainWindow()`.

The first attempt started the socket after `await createMainWindow()` and timed out before socket creation; that configuration is **not acceptable** for integration. The second attempt moved socket startup before the window await and returned exit **0** after 5.65 seconds.

Observed output:
```text
HEALTH: {"service":"daube-browser-control-v1","transport":"unix-socket","mode":"pilot"}
UNALLOWLISTED_INSPECT_STATUS:503
NAVIGATION_RESULT: {"navigated":true,"url":"https://daube-hybrid-staging-v1.spacew039.workers.dev/health"}
INSPECT_RESULT: {"tab":{"url":"https://daube-hybrid-staging-v1.spacew039.workers.dev/health", ...}}
STAGING_ELECTRON_INTEGRATION_PASS
```

The returned tab text contained Cloudflare staging status `ready`. The socket was local, mode 0600, and temp profile, Xvfb and Electron were torn down via trap after the test. Original `daube-sovereign-browser.service` remained untouched and running.

## Integration pattern (not yet applied to production Electron)
- In `electron/main.cjs` add `const { startControlSocket } = require('./browser-control.cjs');`
- Within `app.whenReady`: `await loadCore(); installIpc(); await startControlSocket({activeTab,socketPath,navigate}); await createMainWindow();`
- Bind socket only under `/run/daube-sovereign/`, mode `0600`; ensure the service user owns the directory.
- Use URL allowlist / read-only inspection only, no arbitrary page-JS or shell input.
- Stop service if socket fails to initialize, rather than silently continuing as if automation were enabled.
- Deploy through an authorized application release gate. Current SentinelX file_ops grants only read permission to `/opt`.

## Remaining HOLD
1. No production Electron socket installed/read back.
2. No authenticated Google Cloud A claim to Cloudflare Durable Object.
3. No real GCP A→B failover; only Cloudflare internal simulated-A probe PASS.
4. GitHub Actions required check absent; independent GCP exact-SHA QA PASS is a different gate.
