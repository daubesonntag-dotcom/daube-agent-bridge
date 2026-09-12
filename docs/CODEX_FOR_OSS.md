# Codex for Open Source readiness

Official program: https://openai.com/form/codex-for-oss/

BRIDGE² is maintained as a real interoperability project first. Program eligibility is treated as a consequence of useful open-source maintenance, not as the project goal.

## Current public evidence

- Public MIT repository owned by the primary maintainer.
- v0.1.2 release with wheel, MCPB, SHA256SUMS, and shim-free module entrypoint verification.
- Official MCP Registry entry is active/latest at `io.github.daubesonntag-dotcom/daube-agent-bridge`.
- Release gate: 7 tests, Ruff clean, 7 target families, 13 generated artifacts.
- Deterministic MCPB packaging and official `mcp-publisher validate` verification.
- Security policy, contribution guide, release receipts, roadmap issues and good-first-issue work.
- External discovery PRs are open against MCP and Claude ecosystem lists.

## Maintenance responsibilities

The primary maintainer owns the portable skill spec, compiler targets, MCP/MCPB packaging, issue triage, contributor review, releases, security policy, registry metadata, and provider compatibility fixtures.
## Application posture

OpenAI states that it looks for active maintainers, meaningful usage or broad adoption, or clear ecosystem importance. BRIDGE² is still early-stage, so applications must report adoption honestly and emphasize concrete maintenance evidence and interoperability value.

Private account identifiers and exact application answers are kept outside the public repository in the ignored local build workspace.

## Evidence to strengthen next

- Real package/install telemetry.
- Non-maintainer issues and pull requests.
- Provider compatibility break/fix history.
- More release cycles with reproducible verification.
- External integrations, tutorials and retained contributors.
