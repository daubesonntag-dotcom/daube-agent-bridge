# BRIDGE² Ultimate Master Execution Map

**Spec:** `docs/superpowers/specs/2026-09-12-bridge2-ultimate-architecture-design.md`

**Purpose:** Sequence the approved 0.2→1.0 architecture into independently reviewable implementation trains. Each train gets its own detailed TDD plan immediately before execution; no later train starts until the previous train's exit gate is evidenced.

## Dependency order

```text
0.2 Semantic Core
  ↓
0.3 Conformance
  ↓
0.4 Runtime
  ↓
0.5 Apps & Tasks
  ↓
0.6 Studio Alpha
  ↓
0.7 Adapter SDK + TypeScript parity
  ↓
0.8 Supply Chain
  ↓
0.9 Ecosystem Beta
  ↓
1.0 Stable Standard
```

The trains are dependency-ordered rather than calendar-ordered. Independent research/distribution work may happen in parallel, but no implementation may depend on an unverified future contract.

## Train contracts

| Train | Deliverable | Required evidence before next train |
|---|---|---|
| 0.2 | Provider-neutral IR, diagnostics, adapter ABI, compatibility facade | 15 v0.1.3 artifacts preserved by golden regression; public CLI/MCP API unchanged |
| 0.3 | Immutable profiles, capability resolver, compatibility states, conformance corpus | Every built-in target ≥ C2 for covered fixtures; silent degradation impossible |
| 0.4 | Stateless runtime boundary, extension bus, execution/risk policy | stdio and HTTP regression suites pass from the same core |
| 0.5 | MCP Apps target, ExecutionHandle/Tasks, human-input states | Real Apps/Tasks fixtures pass; unsupported hosts degrade explicitly |
| 0.6 | Local Studio Alpha: Visual Compiler, Radar, artifact diff | author→compile→inspect works without duplicating compiler logic |
| 0.7 | External adapter SDK and TypeScript parity | one out-of-tree adapter passes conformance; TS matches Python golden corpus |
| 0.8 | Provenance/signing-ready release pipeline | deterministic build + provenance verification are reproducible off GitHub Actions |
| 0.9 | Federated catalog metadata, BIPs, contributor flows | evidenced external usage/contribution; trust facts distinguish DECLARED/VERIFIED/OBSERVED |
| 1.0 | Stable Skill Spec v1 / IR v1 / Adapter API v1 / Conformance Spec v1 | migration guarantees tested; ≥1 external adapter and ≥1 external consumer; built-ins C3 where applicable |

## Cross-train invariants

- Python remains the reference implementation until parity is proven by the golden corpus.
- `skill.yaml`, `compile_spec()`, the CLI, and the existing MCP tools remain compatible unless a documented migration explicitly replaces them.
- Provider syntax stays out of canonical IR.
- Compilation remains offline/deterministic by default.
- Semantic loss is always diagnosed as EXACT/ADAPTED/DEGRADED/UNSUPPORTED in the train where capability resolution exists.
- Base installation must not pull Studio/browser automation/database/enterprise-auth dependencies.
- GitHub Actions is an optional executor; canonical gates must run locally or self-hosted.
- Custom package registry, custom OAuth server, marketplace billing, and custom VM sandbox remain out of scope.

## Planning discipline

A separate detailed implementation plan is authored for each train before code changes for that train begin. The first executable plan is:

- `docs/superpowers/plans/2026-09-12-bridge2-0.2-semantic-core.md`

Every detailed train plan must:

1. map exact files and interfaces before task decomposition;
2. use TDD for behavior changes;
3. end each task with an independently reviewable commit;
4. run the repository gate before claiming train completion;
5. update the master map only when an exit gate is actually evidenced.

## Parallel lanes that do not block core trains

Distribution PRs, directory submissions, benchmark research, documentation, and OSS program applications may continue in parallel when they do not mutate unapproved compiler/runtime contracts. Authentication, payment, CAPTCHA, private identity, and destructive actions remain explicit human gates.

The master execution order is therefore strict for architecture dependencies but permissive for independent ecosystem work.