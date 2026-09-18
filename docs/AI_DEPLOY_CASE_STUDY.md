# D’AUBE // BRIDGE² — AI Deploy Network Case Study Source

## Publication context

- Deployment: **D’AUBE // BRIDGE² — Universal AI Skill Compiler & MCP Bridge**
- AI Deploy Network status: **Approved** on 2026-09-18
- Evidence level: AI Deploy Network Approved deployment record
- Release baseline: v0.1.3
- Client: No external client; this is a D’AUBE SONNTAG open-source engineering deployment
- Claim boundary: this case study reports implementation and technical-operational outcomes only. It does **not** claim client-confirmed hours saved, cost savings, revenue impact, production uptime, adoption volume, or commercial ROI.

## Client / builder situation

D’AUBE was maintaining AI capabilities across a fragmented ecosystem of provider-specific integration formats: MCP tools, OpenAI/Codex skill and function definitions, Claude plugin and skill surfaces, Gemini skill/tool files, DeepSeek and Meta/Llama tool schemas, and browser-extension manifests.

The underlying capability was often conceptually identical, but each provider required a different packaging shape. Maintaining those definitions independently created duplicated engineering work, compatibility drift, inconsistent validation and a larger release-verification surface.

The engineering goal was therefore not to hide provider differences. It was to define a capability once in a provider-neutral form, validate it explicitly, and generate provider-specific outputs that remain human-readable and auditable.

## Implementation journey

BRIDGE² was implemented as a Python 3.11+ compiler around a portable YAML capability specification.

The implementation path was intentionally evidence-first:

1. Define one portable source specification for capability metadata and tool behavior.
2. Validate the source before any provider artifact is generated.
3. Compile the validated specification into explicit target-specific files.
4. Keep every generated artifact text-first and diffable.
5. Expose the compiler through a FastMCP server with bounded operations for target discovery, validation and compilation.
6. Add release gates for tests, Ruff, deterministic packaging, package hashes, isolated wheel execution and MCP Registry validation.
7. Publish the release through normal open-source distribution surfaces rather than treating an internal build as evidence.

Release v0.1.3 generates **15 deterministic artifacts across 7 target families**:

- MCP
- OpenAI / ChatGPT / Codex
- Claude
- Gemini
- DeepSeek
- Meta / Llama
- Chromium browser integrations

The release verification receipt records:

- 15/15 automated tests passing
- Ruff clean
- 15 generated sample artifacts
- deterministic MCPB packaging
- published SHA-256 hashes
- valid MCP Registry metadata
- isolated wheel smoke test passing
- git diff check passing

## Key decisions

### 1. One semantic source, explicit provider adapters

BRIDGE² does not force every provider into one opaque runtime abstraction. The portable capability definition is the source of truth, while provider-specific adapters generate the exact files expected by each ecosystem.

This makes divergence visible instead of silently normalizing it away.

### 2. Human-readable output over opaque generation

Generated files are designed to be inspectable, reviewable and version-controlled.

The operational rule is simple: if an adapter produces unsupported or misleading capability claims, the output should be rejected rather than hidden behind generator logic.

### 3. Authentication stays outside the compiler

BRIDGE² does not store provider API keys.

Authentication and execution authority remain with the target host or provider. The compiler transforms capability definitions; it does not silently execute generated tools.

### 4. Verification before ecosystem expansion

The project deliberately treats release evidence as part of the product.

A target family is more useful when its output can be reproduced and inspected than when a large compatibility list exists only as a declared claim.

### 5. Open-source distribution as the evidence anchor

The public repository, tagged release, package hashes, verification receipt and Official MCP Registry record are the primary external evidence surfaces.

## Lessons learned

### Portability is primarily a semantics problem

Generating files is straightforward compared with preserving meaning across provider-specific constraints.

The important engineering layer is the semantic model and validation boundary, not the template renderer.

### Provider similarity should not be mistaken for provider equivalence

Many AI ecosystems expose tools, skills or plugins that appear structurally similar but differ in naming, packaging, lifecycle and supported behavior.

BRIDGE² therefore keeps provider adapters explicit rather than assuming interchangeability.

### Determinism materially improves reviewability

Deterministic artifacts and package hashes make release comparison, debugging and external verification much simpler.

They also create a stronger boundary between “the source compiled successfully” and “someone manually assembled a plausible-looking integration package.”

### Compatibility claims need evidence at the release level

A compatibility matrix becomes unreliable if it is not tied to tests, fixtures, release receipts and provider-specific break/fix history.

Future growth should therefore prioritize stronger compatibility evidence before a larger number of declared targets.

## Technical / operational impact

The demonstrated reference capability is authored once as a portable YAML specification and compiled into **15 integration artifacts across 7 target families**.

The release process establishes a single auditable source of truth for that capability and a repeatable verification path around generated outputs.

For v0.1.3, the recorded technical outcome is:

- 7 target families
- 15 deterministic generated artifacts
- 15/15 release-gate tests passing
- Ruff checks passing
- valid MCP Registry metadata
- deterministic package hashes
- isolated wheel runtime smoke test passing

These are builder-reported technical and operational outcomes.

No client-confirmed time savings, cost reduction, revenue growth or production-scale adoption is claimed.

## Future improvements

The next maturity layer is not simply “more providers.”

Priority improvements are:

1. stronger provider-specific compatibility fixtures;
2. explicit break/fix history when provider schemas change;
3. benchmark receipts for compile latency, throughput and artifact size;
4. more non-maintainer integration tests and contributor examples;
5. richer semantic validation before rendering;
6. clearer compatibility levels so “generated”, “validated” and “runtime-tested” are never conflated;
7. additional tutorials and reference integrations that make adoption independently reproducible.

## Reproduction / evidence references

Repository:
- https://github.com/daubesonntag-dotcom/daube-agent-bridge

Primary evidence in the repository:
- `README.md`
- `docs/VERIFICATION.md`
- `docs/DISTRIBUTION.md`
- `SECURITY.md`
- `docs/CODEX_FOR_OSS.md`

Release:
- v0.1.3

Official MCP Registry identifier:
- `io.github.daubesonntag-dotcom/daube-agent-bridge`

## Publication checklist

Before copying this source into AI Deploy Network:

- keep the deployment linked to the already approved BRIDGE² record;
- preserve the “no external client” context;
- do not convert technical outputs into invented business ROI;
- do not describe draft-PR performance/security documents as merged mainline evidence unless their current repository state is re-verified;
- do not claim production adoption, uptime or customer scale without evidence;
- keep the case study focused on implementation journey, decisions, lessons and technical-operational impact.
