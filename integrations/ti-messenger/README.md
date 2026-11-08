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

## Hosted MCP — actual production HTTPS path (2026-11-08)

Local stdio cannot automatically install into an existing hosted ChatGPT Dot session. A dedicated hosted endpoint was deployed using the **same original Office Messenger Store**:

`https://office-origin.daubesonntag.com/mcp/ti`

This is a stateless MCP Streamable HTTP adapter with the same six tool concepts (status, read, send, verify_reply, audit and sites). It is separate from the historical custom Office `/mcp` endpoint, which has non-standard request headers. OAuth is handled by **Cloudflare Access Managed OAuth**, not a new credential issuer:

- Access app domain restricted to `office-origin.daubesonntag.com/mcp/ti`, app id `983a9992-d0e8-4fb4-b11a-04de19cd1d16`.
- Only existing approved Founder emails or existing Supervisor A/B service identities. Anonymous `/mcp/ti` returns HTTP 401 with valid OAuth protected-resource metadata; existing other Office routes retain their separate Access policies.
- OAuth code + PKCE S256, refresh tokens, 15-minute access-token lifetime and 336-hour grant session; dynamic clients restricted to the ChatGPT connector callbacks and loopback clients. No reusable bearer token in Git.
- Original Gateway directly verifies Cloudflare Access JWT and forwards only signed identity to the same local Office chat API. Human OAuth messages are attributed to their **human** identity, never impersonated as `agent:ti`. A genuine Ti A machine-identity test still requires the actual registered A consumer.
- Source and the root-owned deployed Gateway snapshot are in original `daube-business-os-v2` PR #101; module `deploy/office3d-workstations/agent-chat/hosted-mcp-messenger-v1.mjs`. Local hosted MCP protocol suite 11/11 PASS and Office regression suite 14/14 PASS. The source is live, but authenticated Client OAuth tool discovery and A/B SEND→STORE→READ→ACK are not yet independently verified.

**Connect from ChatGPT web:** Plugins → + → Add custom MCP server → URL above → OAuth → Create as a plugin, then enable the resulting plugin in the authorized session. Connecting always requires a user's account/workspace authorization; a link in Slack or a repository commit cannot silently install an app into another ChatGPT session. The hosted endpoint reduces this to a one-time connection rather than a shell and local MCP registration. Tool write access is controlled by ChatGPT plan/workspace permissions as well as the service's role checks. Do not print authentication credentials in logs or chat.


## 2026-11-08 Canonical machine-client hardening and NextGen adoption

**Most recent source QA overrides earlier README-only descriptions**: original Python machine client was upgraded in this same PR. Actual Host01 isolated Python `29/29 unittest PASS` at exact tested Git blob `b82b4fa8209f1a51901ff944bf65d0c1ddfdf5d7`, test blob `c1304e492524fa7478431d7f16f90918196adb46`; syntax `py_compile` PASS. `install.sh` SHA pins updated to these exact blobs and `sh -n` PASS. This was **source-only QA**, not a live machine A/B send.

- **Bounded source identity:** for original approved A/B Client IDs, a purported server write must echo exactly the expected sender. Regardless of sender it must echo the expected `room=council`, `tenantId=daube`, original `kind`, `clientMessageId` and canonical payload text. Mismatches are `SEND_RECEIPT_INVALID`, not `STORED_BY_SERVER`.
- **Canonical payload first:** reject leading/trailing whitespace as `TEXT_INVALID_OR_NOT_CANONICAL`; callers that maintain an outbox must normalize once **before** computing a digest or writing to disk. Do not silently change the digest on retry.
- **No blind retry:** denied service identity returns `BLOCKED` / `RESTORE_AUTHORIZATION`; ambiguous upstream errors return `UNVERIFIED` / `COLD_READ_BY_UUID_BEFORE_SAME_PAYLOAD_RETRY`; `safeToRetryWithSameId=false` until a trusted controller performs cold readback and verifies original message and payload. Preserve original UUID for any separately authorized retry.
- **No fake actor:** `status()` returns the actual `observedActor` only if supplied by the authenticated server; it reports `actorMatchesExpected=false` if unavailable or mismatched. A successful GET is not evidence of a Ti A/B principal.
- **Exactly one outbox:** Ti/SEC-04 reported 17 offline tests of its local `outbox.py` candidate (SHA256 `6cac6a6ff765f02dbf14f4a5f924881539a7e1c04ea33b0ba74d4cde0ff63f3d`), but the source is **not yet published** to this repository or deployed. Its local filesystem lock is **not** distributed fencing. Do not recreate or overwrite the candidate without an approved source handoff.

The original hosted HTTPS MCP via Cloudflare Managed OAuth is already live and two ChatGPT sessions under the *same Founder OAuth principal* have delivered real send/store/read/ACK; independent A/B service identities remain HOLD. Remote v8 is at 100% on the original Cloudflare Worker, with v7 rollback retained. Neither change makes this local stdio machine-client adapter live or grants original Hybrid's unrelated QA identity.

The repo-wide cross-vendor technology and license review is maintained in the **existing Business OS V2 PR #101**:
[Open harness, Google A2A/ADK, DeepSeek, Meta Messenger and local GGUF admission map](https://github.com/daubesonntag-dotcom/daube-business-os-v2/blob/fix/p0-adapter-offload-20261107/docs/architecture/DAUBE_HARNESS_NEXTGEN_BENCHMARK_2026-11-08.md).
No second orchestrator or background timer is authorized by adopting these references.

### Machine identity verification contract

The portable service-identity client accepts only the existing registered A/B client
IDs. An unknown ID is blocked with `SERVICE_IDENTITY_UNREGISTERED` before HTTP;
configuration is an expected identity, never evidence of the observed identity.
Write receipts must match that expected actor and the exact message ID, text,
kind, room and tenant, including replayed receipts. If a write response also
contains `authenticatedActor`, it must agree. A stored receipt is not delivery.

`status`, `read`, and reply verification now require a server-provided top-level
`authenticatedActor` matching the expected actor. Missing/invalid values produce
`SERVICE_IDENTITY_UNVERIFIED`; a different actor produces
`SERVICE_IDENTITY_MISMATCH`. No message list or authorized-read PASS is returned
for either case. An unknown configured identity is a terminal outbox denial.
Identity failures detected after POST remain uncertain and require reconciliation;
they never prove the write was denied or safe to retry.

**Compatibility HOLD:** older REST responses that contain only `room` and
`messages` no longer pass authenticated reads. The hosted OAuth MCP adapter is a
separate contract and is unchanged. A REST backend must supply its verified actor
before those machine read paths can pass; do not synthesize the field from the
client ID, message senders, or a hosted human session. This source-only change
neither updates that backend nor proves a deployed A/B exchange.

The installer pins are now updated together to the reviewed identity-checked
source and test blobs below. Do not bypass the pin checks; this source-only
installer update does not register a real client or remove the compatibility HOLD.

### Installer validation and failure recovery

`install.sh` validates the exact Git blob bytes for `ti_messenger_mcp.py`
(`34248a98865621528aef4efc780b8438bb185412`) and its named unit test
(`23eb77d2715171e962dbc188565667289cf4168f`). Any future edit to either file
must update these reviewed pins. `tests/test_install.py` checks them against
repository bytes to catch drift. Validation copies only those two files into a
private directory and uses Python isolated mode; extra clone-local tests and
`sitecustomize.py` are not executed. The installed payload contains only the
verified client, not the clone's other files.

On POSIX, the public install path `~/.local/share/daube-ti-messenger` is an
atomically created symlink to a private, mode-0700
`~/.local/share/.daube-ti-messenger.XXXXXXXX/repo` directory. The MCP command path
is unchanged; the launch command adds Python `-I` isolated mode. The operating
system Python installation and its system site configuration remain trusted. Existing paths, including dangling symlinks, are refused. Failed
cloning, pins, validation or preflight clean only this run's staging directory;
a competing install path is not overwritten. Catchable HUP/INT/TERM before
promotion do the same. After publication the payload is retained, including
the short interval before registration; rollback never unlinks the public path. SIGKILL, power loss and filesystem errors can leave
staging behind; inspect before manual cleanup.

Before cloning and again just before registration, `codex mcp list --json` must return an array of named entries,
with no `daube-ti-messenger` entry. Unreadable or unsupported CLI output is a
HOLD, never treated as absence. This contract follows the
[official Codex CLI tests](https://github.com/openai/codex/blob/main/codex-rs/cli/tests/mcp_list.rs).
The actual target CLI version has not been tested here. Real Codex list commands
may perform OAuth discovery for already configured servers; real installation
requires authorization for the clone, configuration reads, any resulting
network access and MCP registration. The offline tests use fake git/Codex only.
Do not edit MCP configuration concurrently with installation: the CLI offers no
compare-and-set registration transaction, so a preflight cannot exclude a
concurrent external configuration writer.

Once `codex mcp add` starts, even an error or interruption can mean the entry was
written. The installer therefore retains the symlink and its private payload,
returns failure/HOLD when add or readback fails, and never automatically removes
an MCP entry or restores an old config snapshot. Inspect `codex mcp get daube-ti-messenger --json` and the referenced path before retrying or performing manual
rollback. An error does not establish that registration failed to persist.
Without Codex, validated source is retained with a HOLD notice for manual client
setup. Readback requires the exact name, enabled status, stdio transport, `python3`
command and `[-I, installed_path]` arguments, as emitted by the
[official CLI implementation](https://github.com/openai/codex/blob/main/codex-rs/cli/src/mcp_cmd.rs).
A successful CLI readback establishes only local registration, not hosted
Ti availability, authorized HTTP access, recipient delivery or a durable ACK.

Offline regression command (no production install or real registration):
`python3 -m unittest discover -s integrations/ti-messenger/tests -v`.

### Explicit outbox result adapter (source-only)

The reviewed send result now retains validated persisted `text` and `kind` so the
optional outbox candidate can independently bind the full returned payload.
`outbox-candidate/messenger_adapter.py` wraps the existing `Client.send`; it does
not create a second transport. It checks queued/configured actor equality before
HTTP and maps a complete exact receipt to STORED. Status alone, incomplete
receipts, contradictory identity after POST, and transport ambiguity remain
UNCERTAIN; this adapter never authorizes automatic retries. Input provenance
must be the actual reviewed Client.send output, not an arbitrary dictionary.
See the outbox README for the fixed council/daube scope and trust boundary.

This adapter is not registered, installed, scheduled, or connected by this
change. The installer continues to execute only its pinned client smoke test;
its source/test pins are updated to the additive receipt-output change. The
outbox adapter requires its own source review and explicit runtime integration.
