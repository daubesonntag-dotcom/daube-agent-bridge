# Changelog

All notable BRIDGE² changes are documented here. The project follows semantic versioning while APIs are young; breaking changes are called out explicitly.

## v0.1.2 — 2026-09-12

- Added shim-free `python -m daube_bridge ...` CLI execution.
- Made release verification source-local to prevent stale editable checkouts or worktrees from being verified accidentally.
- Added regression coverage for module entrypoint, verifier checkout targeting, and Registry title Unicode integrity.
- Verified isolated installation from the public GitHub Release wheel.
- Published deterministic MCPB artifact and SHA-256 receipt.

## v0.1.1 — 2026-09-12

- Added MCPB v0.4 packaging with cross-platform `uv` runtime metadata.
- Published `io.github.daubesonntag-dotcom/daube-agent-bridge` to the official MCP Registry.
- Fixed local MCP module execution to use stdio while keeping `daube-bridge serve` as HTTP.
- Added deterministic MCPB build and registry validation tests.

## v0.1.0 — 2026-09-12

- Initial public release.
- Seven target families and 13 generated integration artifacts.
- FastMCP tools for target discovery, skill validation, and in-memory compilation.
- Claude plugin, provider adapters, browser control surface, release verification, and contribution/security scaffolding.
