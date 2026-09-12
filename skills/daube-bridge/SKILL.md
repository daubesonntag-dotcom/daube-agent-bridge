---
name: daube-agent-bridge
description: Compile one portable AI capability spec into artifacts for MCP, Claude, Gemini, DeepSeek, Meta/Llama and browser agents.
---

# D'AUBE // BRIDGE²

Use this skill when a capability must be portable across multiple AI agent ecosystems.

## Workflow

1. Express the capability as a YAML spec with `name`, `version`, `description`, and `tools`.
2. Validate with `daube-bridge validate <spec>`.
3. Compile with `daube-bridge compile <spec> -o dist`.
4. Prefer MCP where the host supports MCP directly.
5. Use generated native-adjacent artifacts only for the target that understands them.
6. Never claim a provider has a native plugin marketplace or feature unless it actually does.

## Design rules

- Keep business logic provider-neutral.
- Keep tool schemas small, explicit, and typed.
- Treat generated adapters as transport/configuration layers, not new model capabilities.
- Require explicit authentication for sensitive or user-specific actions.
- Fail closed when a requested target cannot represent a capability safely.
