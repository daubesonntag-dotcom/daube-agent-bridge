# D'AUBE × Ti Messenger — portable MCP plug-in v0.1

**Purpose:** Let Ti's authorized cloud agent send/read messages to D'AUBE using the *existing* Messenger on Council/Remote/Office. No interactive browser login is required for a machine identity; **Cloudflare Access service authentication is still required**. No new account, scheduler, background bot, listening port, signing key or Mission Store.

## Install on Ti's cloud computer

1. Retrieve this folder (or the ZIP), put it in a private working directory. Python **3.11+**; no pip packages needed.
2. Provide Ti's *already authorized* Cloudflare service identity from its machine's secret store as environment variables `DAUBE_TI_CF_ACCESS_CLIENT_ID` and `DAUBE_TI_CF_ACCESS_CLIENT_SECRET`. **Do not send these credentials to Slack, ChatGPT or GitHub.** Installation cannot mint or copy them. Existing machine policies must permit the relevant Messenger operation.
3. Configure the exact URL for each enabled website backend:
   - `DAUBE_TI_COUNCIL_MESSENGER_ENDPOINT` — Council's existing authorized machine Messenger API URL, if a room grant and endpoint have actually been deployed.
   - `DAUBE_TI_REMOTE_MESSENGER_ENDPOINT` — Remote website's existing Messenger API URL, if deployed.
   - `DAUBE_TI_OFFICE_MESSENGER_ENDPOINT` — known Office origin API (default in the config). Machine auth and Office tunnel must both be working.
   These must be HTTPS on `council.daubesonntag.com`, `remote.daubesonntag.com` or `office-origin.daubesonntag.com` and follow the exact `/api/agent-chat/.../messages` pattern. No arbitrary host forwarding or redirects.
4. Register this as a **stdio MCP server** with a desktop/cloud agent that supports local MCP processes: use `python3 /.../ti_messenger_mcp.py` and the example MCP config. For Claude Code or Codex configure the local MCP command; for ChatGPT custom Plugins a hosted HTTPS or secure MCP tunnel is required, with explicit owner installation/connection. Installing on Ti's cloud computer depends on the machine's actual tools and permissions.
5. Call `daube_messenger_status` for Council and Remote. Only call `daube_messenger_send` after status returns `READABLE`. Test `send` → store receipt → fresh `read` → counterparty sends `ACK <messageId>` → `verify_reply`.

## Tools

- `daube_messenger_status(surface)` — reachability, auth, and read-contract check.
- `daube_messenger_send(surface, text, kind?, clientMessageId?)` — sends a single message to an existing room, returns the idempotency ID. Reuse that ID on uncertainty. Does **not** claim recipient delivery.
- `daube_messenger_read(surface, limit?)` — recent messages visible to the authenticated Ti identity.
- `daube_messenger_verify_reply(surface, messageId, sender)` — looks for a reply by a *different* persisted actor with `ACK <messageId>`; this is not a Checker signature.
- `daube_messenger_sites()` — Council/Remote/Office web links.

## Production limitations verified on 2026-11-07

- The existing Host01 Office auth gateway is running, but `DAUBE_MESSENGER_MACHINE_AUTH_ENABLED=0`, and its Office tunnel is inactive. It currently returns HTTP 401 without a signed Cloudflare Access assertion.
- The Cloudflare Hybrid Council *machine* chat policy has `enabled: false`, `roomId: null`, and no activated grant. Enabling it requires the original verified machine grant; it cannot be activated merely by a plugin.
- A public authenticated Machine Messenger endpoint on **Remote** has not been established. The Remote URL must be left empty until the website owner deploys that API.
- The current plugin is **source/installable**, not proof of a live Council↔Remote two-way message. Its HTTP client fails closed on sign-in redirects, missing credentials, disabled origin, or wrong API schema. Website UIs continue to enforce their own access for human users.

## Verification

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile ti_messenger_mcp.py
```

Never store service token secrets in this repository or in chat content. In MCP server responses, remote HTTP errors are reduced to bounded codes; credentials and server HTML are not echoed. A remote HTTP 200 login form is not counted as a Messenger read.

**Source owner:** existing D'AUBE BRIDGE². **Coordination:** original ONE-PROGRAM work key `DAUBE-SPRINT-20261028-ONE-PROGRAM`, original D1 mission `2fa20aca-bf79-5aa8-9cad-0a22d971ff34`. Messenger messages are not owner ACK, signed grant/lease or Council approval.