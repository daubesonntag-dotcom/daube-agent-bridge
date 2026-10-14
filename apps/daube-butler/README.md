# D'AUBE Butler — isolated MCP Worker v0.2.1

**Status:** SOURCE STAGED / REVIEW REQUIRED. This folder is an additive module; **do not merge** until independent review and release gates permit it.

## Verified deployment

- MCP endpoint: https://daube-butler-readonly-v021.spacew039.workers.dev/mcp
- Website: https://daube-butler-readonly-v021.spacew039.workers.dev/
- Privacy: https://daube-butler-readonly-v021.spacew039.workers.dev/privacy
- Terms: https://daube-butler-readonly-v021.spacew039.workers.dev/terms
- Support: https://daube-butler-readonly-v021.spacew039.workers.dev/support

Cloudflare Workers on a **new isolated Worker**; no production D'AUBE or Amadeli routes were modified. Source of the deployed Worker is in `worker.js` in this directory. An authorized remote source copy resides at `/opt/daube/work/daube-butler-readonly-v021.js`.

## Tool contract

Exactly five stateless tools: `classify_task`, `suggest_route`, `draft_handoff`, `explain_authority`, `check_receipt`. All are advisory and annotated read-only. No OAuth, account access, task registry mutations, plugin invocation, background watcher, transaction, message sending or public posting.

Operational constraints: D_AUBE scope only; bounded inputs; simple secret filtering; no stored user data; no runtime executor permission. High-risk and mutation-intent operations stay HOLD.

## Evidence observed 2026-10-15 ICT

- Remote Linux Node fetch `/health`: HTTP 200 with `mode=read-only` and `external_action_authorized=false`.
- Live MCP `initialize`: HTTP 200, negotiated protocol `2025-06-18`.
- Live `tools/list`: HTTP 200, five expected names.
- Live `tools/call`: `classify_task` => `PREPARED_FOR_REVIEW`; `suggest_route` => `ADVISORY_ONLY`; `draft_handoff` => `DRAFT_NOT_SENT`; `explain_authority` for production => `HOLD`; `check_receipt` => `EXTERNAL_READBACK_REQUIRED`.
- Website /privacy /terms /support all HTTP 200 with HTML.
- Related Python policy reference: 32/32 local tests PASS, not a substitute for JS Worker independent review.

## OpenAI submission boundary

Previous OpenAI `daube-butler` 0.1.0 was skills-only and remains unchanged. Use a **new With MCP** draft with this HTTPS endpoint and publicly reachable docs. OpenAI scanner, domain token challenge, developer-identity verification and submission review **have not been confirmed**. Do not claim acceptance/publishing.

## Security follow-up

Review Cloudflare security log retention and published Privacy wording, rate limiting and operational usage limits; test official MCP Inspector, negative input payloads, origin/CORS behavior, initial response headers and OpenAI scanner. Attach approval receipt, exact source SHA, domain verification token and rollback evidence before any broad public release. The `.workers.dev` host is a testing origin; the branded domain mapping was not attempted after a safety gate blocked that action.

No GitHub Actions, watcher, paid service, credential, auto-merge, production release, or irreversible action was added.
