# D’AUBE BRIDGE² — OSS Harvest & Founder-Sovereignty Gate

**Status:** DRAFT / REVIEW ONLY — not installed, merged or production activated.  
**Owner:** existing BRIDGE² Capability Scout / D’AUBE Governance.  
**Project isolation:** D’AUBE only. Never promote components to AMADELI or another project by implication.

## Purpose

Turn authorized public-source research into one reproducible, rights-aware **sandbox review packet**, while ensuring no AI, agent, MCP response, skill, upstream template, or workflow can use this route to demote, delete, lock out, replace or bypass the D’AUBE Founder.

The canonical enterprise governance remains D’AUBE's `registry/DELEGATED_CONTINUOUS_IMPROVEMENT_POLICY.json` in `daube-business-os-v2`, with its D0–D4 delegated permissions and D4 Founder-only reserved triggers. **This adapter is not a second approval authority.** The Founder-rights invariant in `oss_harvest.py` is *non-configurable*; additional request fields such as `founder_approved`, `override_policy` or `allow_install` are rejected.

## Implemented path (additive; no new worker)

`authorized public source -> existing capability_scout.scout() -> candidate pin/license -> oss_harvest.assess_harvest() -> sandbox-review receipt -> independent QA/security/legal -> existing governance/Founder decision`.

Only two requests are recognized: `research` (D0 metadata) and `prepare_sandbox` (D1). The latter consumes **local bytes** of a previously collected source file plus the repository-root LICENSE, checks both actual Git blob hashes against pinned declarations, restricts target to `sandbox/oss/<slug>`, and reports SHA-256 digests rather than contents. It never fetches, sends, installs, executes, applies a patch, merges a PR, modifies a service, changes permissions, contacts customers or spends money. No node/browser/SDK/cloud execution is introduced.

Reserved and consequential actions, including founder removal, role changes, ownership transfer, policy bypass, self-approval, production merge/deploy, payment/provider changes and customer contact, return `FOUNDER_ONLY_STOP`. Unknown actions return `ACTION_NOT_DELEGATED`. Even `D1_SANDBOX_REVIEW_PACKET` means only that **supplied local bytes match pinned blob IDs**, not cryptographic GitHub publisher verification, license clearance, trusted code, sandbox execution permission, Founder approval or commercial profit.

## First actual MIT component placed in quarantine

Selected component: [GitHub Spec Kit plan template](https://github.com/github/spec-kit/blob/6c62e10d5ab1d676c557eb2d0cee86be52c893d2/templates/plan-template.md). It is useful for structured project planning, scope, acceptance and QA, but **no productivity uplift is claimed without downstream benchmark**.

| Evidence | Exact reference observed from GitHub | Local reviewed copy |
| --- | --- | --- |
| Upstream commit | `6c62e10d5ab1d676c557eb2d0cee86be52c893d2` | `examples/oss_harvest/spec-kit.review.json` |
| Template Git blob SHA-1 | `36f2eab16880bac670fe43cbe7ef2b9bc8c3aa2f` | `examples/oss_harvest/upstream-spec-kit/plan-template.md` |
| Root MIT LICENSE Git blob SHA-1 | `28a50fa22639e32febe14e4ffc7a732b0ba8c90a` | `examples/oss_harvest/upstream-spec-kit/LICENSE` |
| Review destination | No privileged target | `sandbox/oss/spec-kit-plan` (proposal only) |

The complete original MIT copyright/permission notice is retained alongside the text. No upstream hooks, executables, post-install scripts or commands are used. No third-party source is silently copied into BRIDGE² production code or a paid client deliverable. A repo-root MIT notice is not a blanket license for every nested asset: independent legal review remains necessary before any downstream distribution.

## Verification commands

```bash
PYTHONPATH=src python -m pytest -q tests/test_oss_harvest.py tests/test_capability_scout.py
PYTHONPATH=src python -m daube_bridge.oss_harvest \
  --index examples/capability_scout/public-reviewed-20261013.json \
  --query 'project roadmap planning spec' --action prepare_sandbox \
  --candidate-id github_repository:github/spec-kit \
  --evidence examples/oss_harvest/spec-kit.review.json \
  --source-file examples/oss_harvest/upstream-spec-kit/plan-template.md \
  --license-file examples/oss_harvest/upstream-spec-kit/LICENSE
```

Expected state: `D1_SANDBOX_REVIEW_PACKET`; `founder_authority_immutable=true`, `external_action_authorized=false`, `production_promotion_authorized=false`, `spend_authorized=false`, `sandbox_execution_authorized=false`, `source_origin_authenticated=false` and `license_compliance_verified=false`.

Test-first local evidence: initial stub produced 38 failing cases/1 passing case; after implementing a minimal gate, 39/39 passed. A second red-team round uncovered three unsafe admission cases (secret-like source, founder-removal text, invalid UTF-8). After fixing, the combined existing Capability Scout and OSS guard suite passed **89/89** on Python 3.13.5. This demonstrates bounded local behavior only. Ruff/full repository pytest, hosted CI and CodeQL still need exact-head verification; prior hosted-runner availability was blocked by [issue #26](https://github.com/daubesonntag-dotcom/daube-agent-bridge/issues/26).

## Stop/promotion rules

- **D0:** public-source research and reproducible notes may proceed under the existing source owner and allowed terms.
- **D1:** isolated code/test/document changes may be proposed on a dedicated Draft PR, with hash/license evidence and readback; no merge or deploy.
- **D2:** only the canonical policy and exact-head tests, independently green CI, review and rollback can authorize nonmaterial promotion. The OSS guard cannot self-promote or self-approve.
- **D3/D4:** Founder approval/Founder-only authority for material changes, vendor/spend/legal/customer commitments, identity, credentials, ownership, Founder controls and core governance. An explicit Founder stop instruction overrides the queue immediately.

**Important limitation:** a Python preflight and an `AGENTS.md` rule do not secure every account, cloud admin role, database RLS policy or external AI provider. Durable Founder protection also needs platform-native immutable/safe ownership roles, approval enforcement, audit logs and recovery. These infrastructure controls are separate, review-gated work and were not deployed here.

## Next automatic iteration within existing owners

Use the already running D’AUBE research/acquisition loop, not a new agent or watcher. When a **real business problem** benefits from upstream OSS, gather a small license/commit-pinned snapshot, run Capability Scout and this review gate, then benchmark one bounded candidate in a quarantined environment. Promote only with existing governance evidence. If sources are stale, license is unknown, cost is unapproved, security fails, current owner is disputed or Founder authority would change, STOP and report exactly that blocker. No autonomous retry after uncertain external side effects.
