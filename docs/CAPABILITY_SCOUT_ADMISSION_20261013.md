# D’AUBE // BRIDGE² — Capability Scout v1: Cross-Specialism Discovery and Admission

**Date:** 2026-10-13. **Status:** SOURCE-ONLY / DRAFT / HOLD. **Project:** D’AUBE Sonntag exclusively. **Owner:** existing BRIDGE² compiler/agent-interoperability owner; business qualification remains with the existing D’AUBE Revenue/Client Delivery owners. No new task executor, background scraper, CRM, payment worker, marketplace account or paid integration is authorized.

## Objective

Make D’AUBE faster at **finding**, **matching** and **evaluating** specialist capabilities before taking on a task. This is a research-admission primitive, **not** an autonomous skill installer, model upgrader, certification, commercial agent or live network connector. It must not convert metadata from GitHub, a SKILL.md, an A2A Agent Card or MCP Registry into a privilege, a claim of expertise, or a customer promise.

The user-facing business objective is shorter time from a genuine customer problem to an appropriately scoped, evidence-backed solution. D’AUBE may investigate publicly listed sources, compare alternatives, build a bounded sandbox benchmark and suggest an offer through its existing workflow. Actual contracting, paid usage, installation, code promotion and public commitments require their own current authorization and acceptance.

## Research architecture

```text
Authorized public read tools (GitHub / Official MCP Registry / A2A Card / Agent Skills)
  -> small source snapshots with original URL, observed date and optional commit SHA
  -> BRIDGE² Capability Scout v1 (NO network, NO execution, metadata only)
  -> relevant professional domains + review-only ranked candidates + data gaps
  -> existing BRIDGE² compiler / cloud_peer A2A preflight / D’AUBE service catalog
  -> independent source/license/security benchmark -> gated promotion by current owner
```

The implementation is `src/daube_bridge/capability_scout.py`, independent from the compiler and current A2A SDK adapter. It processes structured JSON passed by an authorized collector and prints bounded, deterministic JSON. It never invokes an A2A endpoint, reads a repository's executable skill body or installs a package. The `research_next_step` field is explanatory guidance only; it is not an instruction to an executor.

### Four accepted source shapes

| Input `source_type` | Exact metadata read | Authority boundary |
|---|---|---|
| `agent_skill` | curated Agent Skills frontmatter name, description, optional metadata version/license; GitHub source URL and exact commit SHA | Skill body/scripts/allowed-tools are never ingested or executed; repo-level license does not establish all asset rights |
| `mcp_registry` | a single `GET /v0.1/servers` entry: `server.name`, `description`, `version`, `_meta` status, redacted headers' authentication requirement | registry status is a metadata claim, not an audit; remote auth values and full URL are not emitted; do not connect |
| `a2a_agent_card` | public well-known Agent Card name, version, A2A 1.0 supportedInterfaces, skills' IDs/tags/names | metadata is untrusted; only conservative same-host HTTPS, known HTTP+JSON/JSONRPC bindings are research-eligible; pass through existing `cloud_peer` admission separately |
| `github_repository` | public repo name, description, declared SPDX identifier and topics; optional pinned commit SHA | no claim a package is installable, safe, maintained or legally reusable; independent license/supply-chain analysis remains mandatory |

The snapshot schema is `daube.capability-scout.v1`. Each record needs an explicit `source_url`, timezone-aware `observed_at`, `payload`, and a known `source_type`. Git-based records may add a 40-character lowercase `source_revision`; for pinned `SKILL.md` GitHub URLs the claimed SHA must equal the URL's `/blob/<sha>/` revision. The included public sample is an *edited, minimal, non-byte-identical metadata digest*, not a signed upstream snapshot. The SHA-256 `metadata_sha256` is computed over the normalized sample payload, not the original network response.

### Fourteen bounded domains

| Delivery scope | Domain IDs | Commercial use and review rule |
|---|---|---|
| Engineering quality | `software-qa`, `frontend-ux`, `backend-integrations`, `devops-cloud`, `security-privacy` | Website QA, React fixes, form/API integration and controlled cloud hardening; authorization mandatory for any customer environment |
| AI, data and specialist tooling | `ai-interoperability`, `data-analytics`, `project-management` | A2A/MCP skills, evaluations, dashboards, project planning; do not claim model superiority or production correctness based on listings |
| Design, publishing and demand | `visual-design`, `marketing-growth`, `localization-writing`, `sales-revops` | Licensed visuals, multilingual copy, conversion research, qualified inbound response and QA-backed deliverables; no scraping private contacts, fake testimonials or auto-publishing |
| Finance/compliance | `commerce-finance`, `legal-compliance` | Evidence-based bookkeeping process and requirements research only; tax, legal filing, regulatory and contract conclusions require correctly authorized qualified review |

Matching is deterministic keyword/alias routing in Vietnamese and English. `relevance_score_hint` is a bounded lexical ranking score, **not** confidence, a benchmark, certification, quality rating, forecast of income, or task success probability. If a request falls outside these domains, it must abstain rather than claim an unknown speciality. No task text is returned; only its SHA-256 and matched domain labels are exposed. Do not put customer secrets or contact details into `--query` even on a local machine.

### Verified upstream research anchors (13 October 2026)

The following were inspected from upstream repository metadata, branch commit, and available root LICENSE text. They are **candidates**; no code or skill has been installed or copied into a commercial deliverable:

| Candidate | Exact reviewed upstream ref | Declared repository license | Proposed D’AUBE use | State |
|---|---|---|---|---|
| [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) | `28e4a81a3464475cbccc3c2bbcfe414bcabae32b`; `seo-audit` and `copywriting` SKILL.md frontmatter version 2.2.0 | MIT root LICENSE | SEO/copy QA and landing-page diagnostics | READ-METADATA_ONLY; individual asset/usage scope requires review |
| [wshobson/agents](https://github.com/wshobson/agents) | `46891e7e60da0e52baf1050b7b6391b64e84c6d9` | MIT root LICENSE | Multi-harness engineering skill discovery | READ-METADATA_ONLY |
| [github/spec-kit](https://github.com/github/spec-kit) | `6c62e10d5ab1d676c557eb2d0cee86be52c893d2` | MIT root LICENSE | Spec/roadmap/project planning patterns | READ-METADATA_ONLY |
| [agentskills/agentskills](https://github.com/agentskills/agentskills) | `69ef37e9424c0a7ea9dd2293b559e43ec8176379` | Apache-2.0 root LICENSE; docs may carry different terms | Skill metadata and portability standard | FORMAT_REFERENCE_ONLY |
| [a2aproject/a2a-python v1.2.2](https://github.com/a2aproject/a2a-python/tree/v1.2.2) | tag commit `2f9e44af243df5c7c7a3da361c8d095324bcd5e3` | Apache-2.0 | Reuse existing A2A SDK adapter | EXISTING_DRAFT; separate live-client gate |
| [modelcontextprotocol/registry](https://github.com/modelcontextprotocol/registry) | documented `GET /v0.1/servers` API | licensing transition; check file-level terms, do not infer blanket MIT | public MCP search/delta protocol | DATA_REFERENCE_ONLY |

A real public `GET /v0.1/servers?search=github&limit=3&version=latest` returned HTTP 200 with 3 entries and a `metadata.nextCursor`. Two displayed Smithery-hosted GitHub/Obsidian or PR-analysis entries with remote Authorization headers. The curated sample contains *only a redacted excerpt* of one entry (no token value) and must not be treated as installed, authenticated, vendor-approved, or revenue-producing. Official API documentation: https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/api/official-registry-api.md.

`anthropics/skills` did not expose a root `LICENSE` at the path checked; do not presume licensing for individual skill folders, scripts or images from repository popularity. Source code, generated content and datasets need separate legal rights checks. SPDX identifiers aid discovery, not automatic legal clearance: https://spdx.org/licenses/.

## User workflow and acceptance

```bash
PYTHONPATH=src python -m daube_bridge.capability_scout \
  --index examples/capability_scout/public-reviewed-20261013.json \
  --query "SEO copywriting landing page conversion"

PYTHONPATH=src python -m daube_bridge.capability_scout \
  --index examples/capability_scout/cross-source.synthetic.json \
  --query "A2A agent security QA testing"

PYTHONPATH=src python -m pytest -q tests/test_capability_scout.py
python -m compileall -q src/daube_bridge/capability_scout.py tests/test_capability_scout.py
```

Expected outputs are `RESEARCH_ONLY` with a bounded shortlist, `NO_GROUNDED_DOMAIN` for requests the taxonomy cannot classify, or `NO_RELEVANT_CANDIDATE`. Malformed input fails to `BLOCKED` with nonzero CLI exit 2. Every candidate stays `SOURCE_REVIEW_ONLY`; `license_verified`, `source_provenance_verified`, `peer_identity_verified`, `execution_authorized`, `external_action_authorized`, `autonomous_install_authorized`, and `settled_revenue_proven` remain false. A declared MIT or Apache license is not an approved downstream redistribution or commercial-use grant without matching source and conditions.

**Local verification:** a test-first stub produced 21 expected failures before implementation; after implementing, 21/21 passed. Adversarial additions reproduced 5 unsafe-type/control/interface failures, 9 revision/slug/source-canonicalization failures, 2 pin/SDD-classification failures and 6 A2A binding failures before corresponding fixes. Final focused source tests: **46/46 PASS** on Python 3.13.5 in the D’AUBE sandbox. A separate seeded 512-case offline mutation sweep produced 353 controlled rejections, 119 metadata-only accepted candidate snapshots and **zero unhandled exceptions**; it does not constitute a general security proof. Source-only snapshot examples passed the CLI test; no network was initiated by the scout itself.

**Not verified:** full repository pytest/Ruff, hosted CI on an exact new SHA, signed provenance, remote A2A identity, open-source dependency audit for actual installation, production runtime, continuous operation, commercial conversion or settled cash. Keep the existing BRIDGE² PR #28 DRAFT/HOLD; do not merge, install, deploy or publish on the strength of this document.

## Next smallest steps by existing owner

1. Have the current BRIDGE² owner inspect the four-source schema and test coverage, then compare the exact PR HEAD to sandbox evidence; solve existing hosted runner restriction before claim of release readiness.
2. Use existing approved public research tools to gather new small snapshots, filter by service/known problem, and use this scout only for *discovery*. Do not create another background watcher or crawler; existing D’AUBE acquisition/research task remains source owner.
3. For the top candidate, verify original exact SHA/file, LICENSE, commercial/redistribution restrictions, dependency CVEs, maintainer/release status, privacy, model/data costs, and a bounded sandbox benchmark against an existing D’AUBE implementation before proposing adoption.
4. Only after a customer-backed problem and authorized contract, promote a bounded capability through current delivery/QA, A2A/MCP admission and external cash-evidence gates. Keep AMADELI and other projects separate.

Proposed metrics (not yet measured): relevant sources in top five after human verification (Precision@5), median time to obtain a scoped usable shortlist, percent licenses and actual source revisions independently reviewed, number of unauthorized actions (must remain zero), benchmark yield after admission, customer-accepted project conversion and provider-settled contribution per hour. Do not report forecasts or vanity metadata counts as income.
