# D'AUBE // BRIDGE² Ultimate Architecture Design

**Status:** Approved design baseline for implementation planning  
**Date:** 2026-09-12  
**Project:** `daubesonntag-dotcom/daube-agent-bridge`

## 1. Decision and product thesis

BRIDGE² will evolve as a dual-track platform: an open interoperability standard/compiler underneath and a premium-quality developer product surface above it.

The architecture is governed by four principles:

1. **Write once. Run across agents.** One portable semantic definition compiles into provider and host integrations.
2. **Intent first. Providers second.** Provider syntax is isolated in adapters and profiles, never embedded in the semantic core.
3. **Evidence over pretending.** Compatibility, security, and distribution claims require reproducible evidence.
4. **Open standard below. Competitive developer experience above.** The kernel stays portable and vendor-neutral while Studio differentiates on usability.

The project will not rewrite v0.1.x from scratch. Existing public APIs remain compatibility facades while the new architecture is introduced incrementally.

## 2. Goals and explicit non-goals

Goals: stable portable semantics, deterministic compilation, capability-aware lowering, conformance evidence, extensible runtime, portable UI, reproducible packaging, and excellent developer UX.

Non-goals for the near term: custom package registry, hosted marketplace billing, custom OAuth server, custom VM sandbox, centralized artifact hosting, or mandatory cloud accounts.

## 3. Six-layer architecture

BRIDGE² is organized as six dependency-ordered layers:

1. **Standard / Kernel** — portable semantic specification.
2. **Compiler** — IR, normalization, capability resolver, target planning, adapters, diagnostics, conformance.
3. **Runtime** — MCP transports, execution policies, extension bus, Tasks, Apps, auth boundaries.
4. **Distribution** — MCPB, plugins, wheels, npm packages, GitHub releases, registries, provenance.
5. **Product Surface** — Studio, Visual Compiler, Compatibility Radar, Inspector, Playground, artifact diff.
6. **Ecosystem** — profiles, adapter SDK, catalog federation, BIPs, trust records, community contribution paths.

Higher layers may depend on lower layers; lower layers must not import product, catalog, growth, or provider-specific UI concerns.

## 4. Portable semantic kernel and BRIDGE IR

The public `skill.yaml` input remains supported. It is parsed into an internal canonical BRIDGE IR before any target-specific logic executes.

IR primitives are: `Skill`, `Tool`, `Resource`, `UI`, `Capability`, `Constraint`, `ExecutionPolicy`, `AuthPolicy`, `Provenance`, and `CompatibilityHint`.

Tool schemas use JSON Schema 2020-12 internally. Provider-specific schema restrictions are handled only during target planning or adapter emission.

The IR must never contain concepts such as "OpenAI tool" or "Gemini skill". Provider names belong in adapters, immutable profiles, diagnostics, and compatibility reports.

## 5. Compiler pipeline and adapter contract

The canonical pipeline is:

`PARSE → NORMALIZE → SEMANTIC VALIDATE → CAPABILITY RESOLVE → TARGET PLAN → EMIT → TARGET VALIDATE → CONFORMANCE → PACKAGE + PROVENANCE`.

Compilation is offline and deterministic by default. Live provider probing is an explicit operation and, when used, writes the resolved profile state into `bridge.lock`.

Every provider adapter implements four operations:

- `probe()` — discover or validate a target profile when live probing is explicitly requested.
- `plan(ir, capabilities)` — lower canonical semantics into a target plan without emitting files.
- `emit(plan)` — generate deterministic artifacts.
- `verify(artifacts)` — validate target syntax and target-specific invariants.

`compile_spec(spec)` remains supported as a compatibility facade that internally routes through the new IR pipeline.

Capability resolution returns exactly one state per capability/target pair: `EXACT`, `ADAPTED`, `DEGRADED`, or `UNSUPPORTED`.

Silent degradation is forbidden. Any semantic loss must appear in diagnostics and the compatibility report.

## 6. Diagnostics and source mapping

One structured diagnostic model is shared by CLI, Studio, MCP App, tests, and automation. Diagnostics include code, severity, source location, target, capability, reason, and actionable suggestions.

Generated artifacts carry source mapping through BRIDGE manifests/provenance so Studio can trace source → IR → target output and target output → source.

## 7. Runtime and extension architecture

The runtime is stateless by default and exposes three modes: `stdio`, `HTTP`, and embedded library execution. Durable state is delegated to explicit task/state adapters rather than hidden in compiler sessions.

An extension bus handles independently versioned features. Extension identifiers use stable names, capabilities, schemas, hooks, and fallback policies. Built-in examples include MCP Apps, Tasks, auth policy, provenance, and compatibility reporting.

MCP Apps is the primary portable UI substrate. BRIDGE IR models UI semantically; host-specific metadata is added only by the relevant adapter.

Long-running work is represented by a provider-neutral `ExecutionHandle` with id, state, progress, result, error, input request, cancellation capability, and provenance. MCP Tasks is one lowering target for this abstraction.

Human interaction is a normal execution state, not an exception. Runtime states may include `INPUT_REQUIRED` and `WAITING_USER` for credentials, approvals, destructive actions, financial operations, or other explicit gates.

Auth remains outside skill business logic. Skills declare requirements and scopes; runtime auth policy provides actual credentials and provider-specific OAuth behavior. Secrets, refresh tokens, PATs, and client secrets never belong in portable skill definitions.

Risk classes are explicit: `READ`, `WRITE`, `EXECUTE`, `EXTERNAL_SIDE_EFFECT`, `CREDENTIAL`, `FINANCIAL`, `ADMIN`, and `DESTRUCTIVE`.

## 8. Developer product surface: BRIDGE Studio

Studio uses one authoring flow: `AUTHOR → UNDERSTAND → COMPARE → VERIFY → RUN → PACKAGE → PUBLISH`.

Its primary workspace is a three-pane semantic view: source on the left, BRIDGE IR in the center, target output on the right, with a diagnostics rail for compatibility, diffs, tests, provenance, and logs.

Studio features are intentionally semantic rather than dashboard-oriented:

- **Visual Compiler** — graph of skills, tools, resources, UI bindings, policies, and constraints.
- **Compatibility Radar** — target-by-capability matrix with explanations for every non-EXACT result.
- **Artifact Diff** — compares provider/profile/compiler changes and identifies why an output changed.
- **Inspector** — connection, tools, resources, Apps/UI, Tasks, auth, and traffic inspection with secret masking.
- **Playground** — account-free sample editing and compilation with no persistence by default.
- **Package Center** — deterministic MCPB/plugin/release packaging from the same compiler outputs.
- **Publish Center** — explicit states: `READY`, `AUTH_REQUIRED`, `USER_INPUT_REQUIRED`, `PUBLISHED`, `FAILED`, `UNSUPPORTED`.

Studio does not duplicate compiler logic. Web, CLI, TUI, and MCP App surfaces consume the same Bridge Core API and diagnostic model.

The design language is restrained: clean developer precision, light glass depth, subtle semantic gradients, accessible text/icons, and no color-only status encoding.

## 9. Ecosystem, catalog, and adapter SDK

BRIDGE² is not a centralized marketplace. Artifacts remain hosted in upstream ecosystems such as GitHub Releases, npm, PyPI, MCP Registry, and project repositories.

The BRIDGE Catalog stores and indexes metadata, compatibility evidence, provenance, and discovery information. Catalog facts are classified as `DECLARED`, `VERIFIED`, or `OBSERVED`.

The catalog federates rather than replaces upstream registries. Official MCP Registry data is authoritative for MCP publication state.

Third-party targets are added through the Adapter SDK rather than edits to compiler core. External adapters receive IR types, diagnostics, capability contracts, fixtures, golden snapshot tools, and conformance runners.

Plugin execution uses three trust levels: built-in adapters may run in-process; verified external adapters run in isolated workers; untrusted adapters run in subprocess/sandboxed execution with explicit filesystem/network permissions.

A custom sandbox platform is deferred. The initial implementation uses standard subprocess isolation and explicit permission policy.

## 10. Conformance and trust

Conformance has five levels:

- `C0 Syntax` — generated output is schema-valid.
- `C1 Semantic` — canonical meaning is preserved or declared degradation is explicit.
- `C2 Interop` — a host/provider fixture can consume the artifact.
- `C3 Reproducible` — identical locked inputs produce byte-identical deterministic outputs where the format permits it.
- `C4 Trusted Supply Chain` — provenance/signature/security gates are verified.

The golden compatibility corpus contains valid, invalid, edge-case, provider, degradation, and regression fixtures. Provider format changes require authoritative documentation plus a fixture before adapter behavior changes.

Trust evolves in stages: deterministic builds + SHA256 → `provenance.json` → Sigstore/cosign-ready signing → SLSA-compatible provenance → C4 certification.

Security posture targets OpenSSF-style baseline practices without depending on a single CI vendor. The canonical quality gate must run locally, self-hosted, or in any CI executor.

Catalog ranking prioritizes conformance, maintenance, security, reproducibility, and documentation ahead of star count. Adoption is a secondary signal, not the trust model.

## 11. Governance

Breaking standard changes use BRIDGE Improvement Proposals (BIPs): `DRAFT → DISCUSSION → ACCEPTED → IMPLEMENTED → FINAL`.

Adapter bug fixes and routine provider compatibility updates do not require a BIP. Spec, IR, adapter ABI, or conformance-contract breaking changes do.

## 12. Repository evolution and versioning

The project remains one Python distribution initially. Internal module boundaries are introduced before package splitting: `core`, `compiler`, `adapters`, `runtime`, `conformance`, `packaging`, and `cli`.

Top-level future-oriented directories are `spec`, `profiles`, `conformance`, `examples`, `studio`, `sdk`, and `docs`. They are created only when they carry real independent content.

Package splitting occurs only when evidence justifies it: external adapter installation, heavy runtime dependencies, TypeScript shared contracts, independent extension cadence, or a bloated base install.

Python remains the reference implementation. TypeScript parity is defined by the shared spec and golden corpus, not by maintaining two independently interpreted compilers.

Version domains are independent: compiler package version, IR version, Skill Spec version, Adapter API version, and Conformance Spec version do not automatically move together.

Provider profiles are immutable and versioned separately under `profiles/<target>/<profile>.yaml`. They describe capabilities, schema dialect, artifact conventions, known degradations, and authoritative references.

`bridge.lock` records the resolved compiler/profile state. Profile updates perform impact analysis before replacing the lock.

## 13. Migration strategy

Migration uses a strangler pattern. The v0.1.x compiler remains available while the IR pipeline is introduced behind compatibility facades.

Before refactoring, all 15 v0.1.3 artifacts are captured as legacy golden fixtures. Each adapter migration must classify output as `BYTE_IDENTICAL`, `SEMANTICALLY_EQUIVALENT`, or `INTENTIONAL_CHANGE`.

An intentional change requires a reason, authoritative provider evidence, a regression fixture, and changelog entry.

Adapter migration order is MCP → OpenAI → Claude → Gemini → DeepSeek → Meta/Llama → Browser. MCP goes first because it is the runtime/distribution backbone; Browser goes last so UI packaging does not distort semantic core design.

## 14. Release train

The implementation proceeds through evidence-gated trains rather than a rewrite release:

| Train | Primary outcome | Exit gate |
|---|---|---|
| `0.2 Semantic Core` | IR, diagnostics, adapter interface, compatibility facade | Current outputs preserved by golden regression |
| `0.3 Conformance` | profiles, resolver, compatibility states, corpus | Built-in targets reach at least C2 |
| `0.4 Runtime` | stateless runtime, extension bus, execution policy | stdio + HTTP regressions pass |
| `0.5 Apps & Tasks` | MCP Apps, Tasks abstraction, human-input states | real Apps/Tasks fixtures pass |
| `0.6 Studio Alpha` | Visual Compiler, Radar, artifact diff | local author→compile→inspect flow works |
| `0.7 SDK` | external adapter SDK + TypeScript parity work | one external reference adapter passes conformance |
| `0.8 Supply Chain` | provenance/signing-ready pipeline | reproducibility + provenance verified |
| `0.9 Ecosystem Beta` | catalog federation, BIPs, contributor flows | external ecosystem usage is evidenced |
| `1.0 Stable Standard` | stable spec and compatibility contracts | ABI/spec freeze criteria satisfied |

Product framing: V1 = Compiler Foundation (`0.2–0.4`), V2 = Developer Experience (`0.5–0.7`), V3 = Ecosystem Standard (`0.8–1.0`).

## 15. Build / adopt / reuse policy

BRIDGE² custom-builds only its moat: IR semantics, capability resolver, adapter ABI, diagnostic model, conformance corpus, and Studio semantics.

It adopts mature foundations for MCP runtime, official protocol schemas/extensions, JSON Schema validation, OAuth, editor/diff/graph primitives, Sigstore, and SLSA-compatible provenance concepts.

Custom OAuth servers, package registries, marketplace billing, and custom VM sandboxes are explicitly out of scope for the release train above.

## 16. Quality gates, performance, and dependency budgets

Quality uses four complementary test classes: unit tests, golden artifact tests, conformance tests, and scenario evals that verify semantic outcomes across targets.

The canonical repository gate is executor-neutral and covers linting, unit tests, golden tests, conformance, packaging, reproducibility, and security metadata checks. GitHub Actions is optional infrastructure, not a project dependency.

Initial performance budgets for small skills are targets rather than hard release blockers: parse+normalize <50 ms, one-target compile <100 ms, all built-in targets <500 ms, diagnostics <100 ms on a normal developer laptop.

The base compiler installation remains lightweight. Browser automation, Studio frontend dependencies, enterprise auth SDKs, databases, and telemetry SDKs must not become mandatory base dependencies.

## 17. Definition of 1.0

BRIDGE² reaches 1.0 only when Skill Spec v1, IR v1, Adapter API v1, and Conformance Spec v1 are stable; migration policies are tested; provider profiles and lock behavior are proven; built-ins reach C3 where deterministic bytes are possible; at least one external adapter and external consumer exist; and security/release/provenance processes are documented.

Studio can evolve independently; UI maturity is not a reason to prematurely freeze the interoperability standard.

## 18. Success metrics and benchmark-informed choices

The north-star metric is successful cross-target compiles per week. Supporting metrics are retained contributors, distinct downstream repositories, release installs/downloads, compilation success rate, compatibility-state distribution, regressions caught before release, external adapter count, issue-to-fix time, and registry/catalog referrals. GitHub stars are a lagging adoption indicator only.

The design intentionally borrows proven patterns without copying whole products:

- Agent Skills: minimal portable skill structure and progressive disclosure.
- Official MCP Registry: machine-readable publication and discovery contracts.
- MCP Apps and Tasks: portable UI and durable execution as extensions rather than bespoke host protocols.
- FastMCP: ergonomic Python runtime and evolutionary package separation.
- Context7: one capability distributed through multiple installation surfaces.
- MCP Inspector: shared core across interactive and automation surfaces plus machine-readable diagnostics.
- Sigstore/SLSA/OpenSSF: staged provenance and supply-chain trust rather than custom security infrastructure.

## 19. Final architecture contract

BRIDGE² Core converts intent into canonical semantics, resolves host capabilities, produces explicit target plans, emits deterministic verified artifacts, and records provenance.

BRIDGE Studio makes that interoperability visible by connecting source intent, canonical semantics, target capability, generated artifacts, and runtime behavior in one workspace.

The ecosystem remains decentralized: artifacts stay in upstream registries and repositories; BRIDGE² adds compatibility evidence, conformance, discovery, and developer experience.

No implementation phase may silently weaken these boundaries for convenience. Changes that alter the stable semantic or extension contracts must follow the BIP path.