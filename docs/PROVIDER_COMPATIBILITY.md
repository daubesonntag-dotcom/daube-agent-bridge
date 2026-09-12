# Provider compatibility

Last reviewed: 2026-09-12.

BRIDGE² treats provider formats as versioned compiler surfaces. Compatibility claims must be backed by authoritative provider documentation and executable fixtures.

## OpenAI / Codex

Generated surfaces:

- `openai/mcp-tool.json` — remote MCP descriptor using `type: mcp`, `server_label`, and `server_url`.
- `openai/functions.json` — function-tool schemas.
- `openai/SKILL.md` — portable skill content for skill-capable agent environments.

Reference: https://developers.openai.com/api/reference/cli/resources/beta/subresources/responses

## Claude

Generated surfaces:

- `claude/.mcp.json` — project-level MCP connection config.
- `claude/.claude-plugin/plugin.json` — plugin metadata.
- `claude/skills/<skill>/SKILL.md` — portable Claude skill content.

Reference: https://docs.anthropic.com/en/docs/agents-and-tools/mcp-connector

## Gemini

Current-format generated surfaces:

- `gemini/mcp-tool.json` — Remote MCP descriptor using `type: mcp_server`, a snake_case server name, and `url`.
- `gemini/.agents/skills/<skill>/SKILL.md` — managed-agent skill discovery path.

Backward-compatible surfaces remain available as `gemini/mcp.json` and `gemini/SKILL.md`.

References:

- https://ai.google.dev/gemini-api/docs/function-calling
- https://ai.google.dev/gemini-api/docs/custom-agents

## Compatibility policy

1. Prefer additive output changes over breaking path changes.
2. Keep current provider shapes covered by focused tests.
3. Record provider documentation used to justify a compatibility change.
4. Do not label a provider surface native unless the provider documents it.
5. When a provider changes format, ship a regression fixture and release note.

Executable coverage lives in `tests/test_provider_compatibility.py`.
