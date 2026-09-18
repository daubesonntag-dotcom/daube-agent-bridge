# BRIDGE² threat model

BRIDGE² compiles portable AI capability specifications into readable integration artifacts. The compiler does not execute generated tool definitions, but its output can later be consumed by systems with real authority. The primary security objective is therefore to prevent a low-trust input specification from silently becoming a high-trust execution path.

## Trust boundaries

1. **Skill specification input** — untrusted until validated.
2. **Compiler core** — trusted transformation layer.
3. **Generated artifacts** — inspectable output, not automatically trusted for deployment.
4. **MCP / provider host** — separate execution environment with its own credentials and permissions.
5. **External content** — potentially adversarial if a downstream agent can ingest web pages, files, messages or retrieved documents.
6. **Human approval boundary** — required before privileged or destructive downstream actions.

## Primary risks

### T1 — Prompt or instruction injection through capability text

A malicious or compromised skill description, tool description, retrieved document or external file could carry instructions that influence a downstream model after compilation.

Controls:

- generated output remains readable and diffable;
- treat descriptions and external content as data, not authority;
- require deterministic validation of expected schemas;
- isolate untrusted external content from privileged system instructions;
- require explicit human approval before high-impact tool execution.

### T2 — Excessive agency downstream

A generated integration can be connected to tools that have broader functionality, permissions or autonomy than the use case requires.

Controls:

- BRIDGE² does not embed provider credentials;
- tool permissions belong to the target host/provider;
- use least-privilege credentials;
- separate read tools from write/delete/admin tools;
- require approval gates for privileged operations;
- disable unused tools and stale integrations.

### T3 — Endpoint substitution or unsafe remote target

Generated MCP configuration may point at an operator-supplied endpoint. If that endpoint is changed or compromised, downstream clients may connect to an unintended service.

Controls:

- endpoint values remain visible in generated text;
- operators must review remote URLs before use;
- production hosts should enforce TLS and origin/authentication policy;
- avoid embedding secrets in endpoint URLs;
- maintain allow-lists where the consuming platform supports them.

### T4 — Malformed or hostile schemas

Unexpected nested structures, very large inputs or malformed parameter schemas can create parser, memory or compatibility failures.

Current control:

- required top-level fields and tool-list shape are validated.

Hardening backlog:

- explicit maximum sizes for names, descriptions, tools and schema depth;
- JSON Schema validation for portable skill documents;
- duplicate tool-name rejection;
- stricter parameter-schema validation;
- fuzz/property testing for hostile inputs.

### T5 — Generated artifact trust escalation

A user may assume generated artifacts are safe because they were produced by the compiler, then deploy them without reviewing provider-specific permissions or semantics.

Controls:

- generated artifacts are text-first;
- compatibility claims must correspond to authoritative provider capabilities;
- release verification covers fixtures and target discovery;
- provider changes require documentation and a minimal reproducible fixture.

### T6 — Supply-chain compromise

BRIDGE² depends on Python packages and release infrastructure. A compromised dependency, build environment or release asset could alter behavior.

Controls already present:

- deterministic MCPB packaging;
- published release-asset SHA256 values;
- isolated release smoke testing;
- source-controlled registry metadata.

Hardening backlog:

- dependency lock/constraint policy;
- software bill of materials for releases;
- signed provenance/attestations;
- dependency vulnerability scanning;
- signed release artifacts when practical.

### T7 — Secret disclosure

Secrets could be placed in skill content, generated configs, logs or public evidence.

Controls:

- BRIDGE² does not store provider API keys;
- do not place tokens in portable skill specifications;
- redact credentials from screenshots, logs and evidence packets;
- keep external platform application answers and private identifiers outside the public repository.

### T8 — Non-deterministic or tampered evidence

Performance or verification claims can become misleading if the environment, revision or inputs are omitted.

Controls:

- release verification receipts record commit/version and hashes;
- performance receipts record environment, input, iterations and deterministic artifact digest;
- do not overwrite historical receipts when methodology or environment changes.

## Red-team scenarios

Before a major release, test at least:

- tool descriptions containing direct and indirect prompt-injection payloads;
- Unicode/confusable names and path-like names;
- duplicate tool names;
- extremely long descriptions and deeply nested parameter schemas;
- endpoint strings containing credentials, unusual schemes or control characters;
- malformed YAML and type confusion;
- repeated compiles to detect non-determinism;
- corrupted release assets and incorrect hashes;
- a downstream host where a generated tool has intentionally excessive permissions;
- stale provider capability fixtures after a provider format change.

## Security acceptance gate

A release should not be promoted when any of the following is true:

- generated output becomes opaque or cannot be audited;
- a new feature requires BRIDGE² to retain provider credentials without a dedicated secret-management design;
- generated artifacts grant authority beyond what the user explicitly configured;
- provider support is asserted without reproducible evidence;
- deterministic release verification fails;
- a high-severity vulnerability has no mitigation or explicit release-blocking decision.

## References

- OWASP Top 10 for LLM and Generative AI Applications, including Prompt Injection and Excessive Agency.
- NIST AI Risk Management Framework and the Generative AI Profile.
- BRIDGE² `SECURITY.md`, `docs/PROVIDER_COMPATIBILITY.md` and `docs/VERIFICATION.md`.
