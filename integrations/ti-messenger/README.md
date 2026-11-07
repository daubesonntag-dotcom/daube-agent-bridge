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
- `daube_messenger_audit()` — live read-only audit that inventories all configured Messenger surfaces and marks each checkpoint `PASS` or `HOLD` while leaving bidirectional delivery `UNVERIFIED` until genuine recipient readback.

## Production status verified on 2026-11-07

- **Office machine room is enabled at the origin**: Host01's existing Office gateway has `DAUBE_MESSENGER_MACHINE_AUTH_ENABLED=1`; existing Cloudflare Access service-token policies bind Ti (Supervisor A) and D’AUBE (Supervisor B). Native signed test JWT cross-room suite passed 11/11 on Node22, but a real authenticated A/B token handshake and recipient readback are still unverified. Unauthenticated calls return 401.
- **Office tunnel is already live via the founder-owned systemd user unit** `daube-office3d-private-connector.service` (`enabled/active`), using an existing local `0600` token and 4 healthy Cloudflare connections. The inactive legacy system unit `daube-cloudflared-office.service` was found to be duplicate and disabled without touching the live user connector. Never manufacture another token or share the existing one.
- Cloudflare Access already permits the registered Supervisor A/B machine principals to reach Council and Remote; the **Council Hybrid application-level room grant** still has `enabled: false`, `roomId: null`, and no activated durable grant. This is a separate gate from Access; a legitimate owner-issued room grant and consumer are required. Do not forge an activation record.
- **Remote Worker currently lacks an `/api/agent-chat` route** in deployed source. Its Access machine allow policy already exists, but it must be connected to the original Messenger store and tested before configuring its endpoint.
- The current plugin is **source/installable**, not proof of a live Council↔Remote two-way message. Its HTTP client fails closed on sign-in redirects, missing credentials, disabled origin, or wrong API schema. Website UIs continue to enforce their own access for human users.

## Verification

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile ti_messenger_mcp.py
```

Never store service token secrets in this repository or in chat content. In MCP server responses, remote HTTP errors are reduced to bounded codes; credentials and server HTML are not echoed. A remote HTTP 200 login form is not counted as a Messenger read.

**Source owner:** existing D'AUBE BRIDGE². **Coordination:** original ONE-PROGRAM work key `DAUBE-SPRINT-20261028-ONE-PROGRAM`, original D1 mission `2fa20aca-bf79-5aa8-9cad-0a22d971ff34`. Messenger messages are not owner ACK, signed grant/lease or Council approval.

## Codex automatic local registration

The reviewed `install.sh` checks the pinned Git source and test blobs, runs the Python test suite, and when a local `codex` binary exists executes the supported command `codex mcp add daube-ti-messenger -- python3 <absolute-installed-path>`. It refuses to replace an existing server and checks `codex mcp get` after registration. This **does not inject credentials**; a pre-approved Ti environment/secret store must supply them. A hosted Ti session that cannot dynamically register local MCP remains blocked until its host allows MCP connection or an approved hosted connector is installed. See <https://developers.openai.com/learn/docs-mcp> and <https://github.com/openai/codex/blob/main/codex-rs/cli/src/mcp_cmd.rs> for current command support.

Updated Host01 isolated MCP code QA: 21/21 Python unittest PASS, and schema/handler self-inventory included as the sixth tool. Negative tests reject missing or blank original message room before counting a counterpart ACK.
