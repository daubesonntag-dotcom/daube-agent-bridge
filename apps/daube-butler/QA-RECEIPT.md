# D'AUBE Butler — test and handoff receipt (2026-10-15)

**Deployment boundary:** one new Cloudflare Worker; no existing routes touched. New plugin draft not yet created or submitted.

| Check | Evidence | Result |
| --- | --- | --- |
| GET /health | HTTP 200, read-only | PASS |
| MCP initialize | 2025-06-18 | PASS |
| MCP tools/list | Five expected tools | PASS |
| classify_task | PREPARED_FOR_REVIEW | PASS |
| suggest_route | ADVISORY_ONLY | PASS |
| draft_handoff | DRAFT_NOT_SENT | PASS |
| explain_authority: production | HOLD | PASS |
| check_receipt | EXTERNAL_READBACK_REQUIRED | PASS |
| GET / /support /privacy /terms | Each HTTP 200 | PASS |
| Python reference tests (separate codepath) | 32 passed | PASS / not Worker conformance |
| Official MCP Inspector | Not executed | PENDING |
| OpenAI Scan Tools | Not executed | PENDING |
| Domain challenge | Portal token not provided | PENDING |
| Independent security / privacy signoff | Not obtained | HOLD |

Source filename: `apps/daube-butler/worker.js` (review branch). Data handling statements must be reconciled to real hosting configuration before broad publication.

No claim of end-to-end plugin deployment or cross-plugin execution.

## Follow-up hotfix — 2026-10-15 ICT

**OpenAI actual finding:** "These server instructions appear to instruct the model to use another plugin or connector." OpenAI Platform marked the scanned server instructions as `Not live`. Connected plugin draft exists under the developer's OpenAI Platform organization, but is **not published**.

**Patch staged in this draft PR:** remove `instructions` field from MCP `initialize` (no cross-plugin directive); add `GET /.well-known/openai-apps-challenge` which returns the configured `OPENAI_APPS_CHALLENGE_TOKEN` binding as plain text. The verification token is **not committed**. All other five tools remain read-only.

**Static independent inspection of the latest source:** JavaScript parse PASS and 8/8 source-policy assertions PASS (no server steering instructions, token binding only, text/plain verification, five tool names, read-only annotations, D_AUBE boundary, no hard-coded challenge, correct draft branch). This is NOT a live deployment test.

**Runtime HOLD:** Cloudflare API attempted hotfix deployment was blocked by the host safety gate. Live Cloudflare Worker `etag` was unchanged when checked. The running endpoint still returns the old initialize instructions until a separately authorized deployment occurs. Do not claim OpenAI warning cleared or domain ownership verified.

**Next authorized release steps:** deploy the exact reviewed source to existing isolated `daube-butler-readonly-v021` Worker; configure the verification token as a Worker secret binding, sourced privately from the OpenAI Platform MCP connection dialog; independent GET readback and MCP initialize inspection; click Verify Domain; rescan tools; independently confirm findings cleared. Review legal support text, host logs/retention and official security gates before submission.
