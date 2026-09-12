# AGENTS.md

## Mission
D'AUBE // BRIDGE² compiles one portable AI skill specification into provider-specific integration artifacts without inventing unsupported provider capabilities.

## Engineering rules
- Keep the compiler deterministic and provider-neutral.
- Prefer authoritative provider docs when formats change.
- Never embed secrets, tokens, credentials, or user data in generated artifacts.
- Add or update tests for schema/adapter behavior changes.
- Run `pytest -q` and `ruff check .` before declaring work complete.
- Generated output must remain readable and auditable.

## Compatibility
Primary targets: OpenAI/ChatGPT/Codex, MCP hosts, Claude, Gemini, DeepSeek, Meta/Llama, and Chromium browser surfaces.

## Maintenance workflow
For provider changes: link authoritative docs in the issue/PR, add a minimal fixture, update the adapter, run the full compatibility gate, and document any behavior change.
