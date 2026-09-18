# ChatGPT plugin readiness

Status baseline: 2026-09-18.

BRIDGE² is being prepared as a public ChatGPT plugin backed by a remote MCP server. This document separates implementation-complete work from external review steps that require a live production host or OpenAI-issued verification data.

## Implemented in this branch

- All three MCP tools expose explicit `readOnlyHint`, `destructiveHint`, and `openWorldHint` annotations.
- All three tools are classified read-only, non-destructive, closed-world, and idempotent.
- `compile_skill` explicitly documents that its endpoint parameter is embedded into generated artifacts and is not contacted by the compiler.
- A public `GET /health` route is available for liveness checks.
- A public `GET /.well-known/openai-apps-challenge` route is available for OpenAI domain verification.
- The challenge route returns the exact `OPENAI_APPS_CHALLENGE` environment value when configured and returns 404 while unconfigured.
- An integration test locks the review-critical tool annotations.

## Annotation justification

| Tool | readOnlyHint | destructiveHint | openWorldHint | Rationale |
|---|---:|---:|---:|---|
| `bridge_targets` | true | false | false | Reads static target/version metadata only. |
| `validate_skill` | true | false | false | Parses and validates caller-provided data in memory; no persistence or external access. |
| `compile_skill` | true | false | false | Compiles caller-provided data in memory. The endpoint string is emitted as configuration text; BRIDGE² does not contact it. |

All three operations are deterministic for the same process version and input, so `idempotentHint=true` is also set.

## Production review gates

These cannot be truthfully marked complete until the production host exists and OpenAI has supplied/accepted the review data:

1. Deploy the HTTP MCP server to a stable HTTPS production hostname.
2. Run the normal BRIDGE² verification gate on the deploy revision.
3. Confirm `GET /health` returns HTTP 200.
4. Confirm MCP discovery reports all tools with the required annotations and titles.
5. Create the ChatGPT plugin draft and run its production MCP scan.
6. Set the OpenAI-issued domain token as `OPENAI_APPS_CHALLENGE` on the production host.
7. Confirm the well-known route returns that exact token, then complete domain verification.
8. Supply public support, privacy, terms, and security/contact URLs.
9. Complete organization/developer verification and ensure the submitting account has the required app-write permission.
10. Submit only after the current production scan is successful.

## Data-handling boundary

The current BRIDGE² MCP tools do not require user authentication, do not persist submitted skill specifications, do not send them to third-party APIs, and do not execute generated tool definitions. Hosting infrastructure can still process ordinary network metadata and operational logs. Any future feature that adds accounts, persistence, external retrieval, write actions, or third-party calls must update the privacy notice, threat model, tool annotations, and review evidence before release.

## Source of truth

The repository, immutable release receipts, verification documentation, threat model, and current production deployment are the source of truth. Marketing copy must not outrun those artifacts.
