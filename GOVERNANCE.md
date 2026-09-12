# Governance

BRIDGE² is currently maintained under a single-maintainer model with public contribution and review paths.

## Maintainer responsibilities

The primary maintainer owns release integrity, portable skill semantics, compiler targets, MCP/MCPB packaging, security policy, registry metadata, issue triage, and contributor review.

## Contribution model

- Issues and pull requests are public by default.
- Compatibility claims require authoritative provider documentation or a reproducible fixture.
- New behavior should include focused tests.
- Security-sensitive changes receive explicit maintainer review.
- Generated artifacts must remain readable and auditable.

## Release gate

A release must pass tests, Ruff, source-local doctor/compile checks, deterministic MCPB generation, wheel build, Registry metadata validation, SHA-256 recording, and a clean Git diff check.

## Decision principles

Portability, evidence, security boundaries, interoperability, and maintainability take precedence over provider-specific shortcuts or vanity metrics.

## Future governance

If sustained external contribution develops, maintainer roles and decision rights may expand through documented, reviewable changes to this file.
