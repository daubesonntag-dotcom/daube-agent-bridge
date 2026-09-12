# Codex for Open Source readiness

Official program: https://openai.com/form/codex-for-oss/

BRIDGE² is maintained as a real interoperability project first. Program eligibility is treated as a consequence of useful open-source maintenance, not as the project goal.

## Current public evidence

- Public MIT repository owned by the primary maintainer.
- v0.1.3 release with wheel, MCPB, SHA256SUMS, provider compatibility fixtures, and shim-free module entrypoint verification.
- Official MCP Registry entry `io.github.daubesonntag-dotcom/daube-agent-bridge` is active with v0.1.3 published as the latest version.
- v0.1.3 release gate: 15 tests, Ruff clean, 7 target families, 15 generated artifacts.
- Deterministic MCPB packaging and official `mcp-publisher validate` verification.
- Security policy, contribution guide, release receipts, roadmap issues and good-first-issue work.
- Three external discovery PRs are open across MCP server, MCP developer-tool, and Claude ecosystem lists.

## Maintenance responsibilities

The primary maintainer owns the portable skill spec, compiler targets, MCP/MCPB packaging, issue triage, contributor review, releases, security policy, registry metadata, and provider compatibility fixtures.
## Application posture

OpenAI states that it looks for active maintainers, meaningful usage or broad adoption, or clear ecosystem importance. BRIDGE² is still early-stage, so applications must report adoption honestly and emphasize concrete maintenance evidence and interoperability value.

Private account identifiers and exact application answers are kept outside the public repository in the ignored local build workspace.

Run `python scripts/adoption_snapshot.py` before submission to capture current GitHub release telemetry and the live Official MCP Registry version without hand-entered vanity metrics.

## Evidence to strengthen next

- Package/install telemetry beyond GitHub release-asset downloads.
- Non-maintainer issues and pull requests.
- Provider compatibility break/fix history.
- More release cycles with reproducible verification.
- External integrations, tutorials and retained contributors.
