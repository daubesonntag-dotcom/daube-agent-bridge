# Distribution ledger

This file records public discovery surfaces for BRIDGE². It intentionally distinguishes shipped/verified listings from pending submissions.

## Active

- GitHub repository: `https://github.com/daubesonntag-dotcom/daube-agent-bridge`
- GitHub release: `v0.1.1`
- Official MCP Registry: `io.github.daubesonntag-dotcom/daube-agent-bridge`
- Registry state verified 2026-09-12: `active`, latest version `0.1.1`

## Pending external listings

- `punkpeye/awesome-mcp-servers` PR #14214
  - Scope: developer tools / MCP servers
  - Status: open; upstream Glama validation remains a prerequisite.
- `ccplugins/awesome-claude-code-plugins` PR #472
  - Scope: MCP Servers / Claude Code ecosystem
  - Status when opened: merge state clean.
## Blocked by external auth

- Glama listing: maintainer GitHub OAuth is required by the submission flow; tracked in issue #9.
- Do not bypass provider authentication, pay for artificial traffic, or manufacture stars/listings.

## Distribution rule

Submit only where BRIDGE² clearly matches scope. Every listing should point to the public repository, reproducible release, and official MCP Registry record.

Prioritize real installs, retained contributors, compatibility fixes, tutorials and downstream integrations ahead of vanity metrics.
