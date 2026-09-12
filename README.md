# D'AUBE // BRIDGE²

> **Write once. Run across agents.**

D'AUBE // BRIDGE² is an open-source universal AI skill compiler and MCP bridge. Define one portable capability spec, then compile it into integration artifacts for ChatGPT/Codex, Claude, Gemini, DeepSeek, Meta/Llama, MCP hosts, and Chromium browsers.

[![Release](https://img.shields.io/github/v/release/daubesonntag-dotcom/daube-agent-bridge)](https://github.com/daubesonntag-dotcom/daube-agent-bridge/releases)
[![MCP Registry](https://img.shields.io/badge/MCP%20Registry-active-brightgreen)](https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.daubesonntag-dotcom%2Fdaube-agent-bridge)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)

## Why BRIDGE²

AI tooling is fragmented. The same capability is repeatedly rewritten as MCP tools, provider function schemas, skills, plugins, and browser configuration. BRIDGE² treats those surfaces as compiler targets while keeping capability logic provider-neutral.

```text
skill.yaml
  |
  +-- MCP tool schema
  +-- OpenAI / ChatGPT / Codex artifacts
  +-- Claude plugin + SKILL.md
  +-- Gemini SKILL.md + MCP config
  +-- DeepSeek tool schemas
  +-- Meta/Llama function schemas
  +-- Chromium extension manifest
```

**Current release:** 7 target families, 13 deterministic artifacts, one MCP server.

## 30-second start

```bash
git clone https://github.com/daubesonntag-dotcom/daube-agent-bridge.git
cd daube-agent-bridge
python -m pip install -e ".[dev]"
daube-bridge validate examples/skill.yaml
daube-bridge compile examples/skill.yaml -o build/sample
```

Run BRIDGE² as a local stdio MCP server:

```bash
python -m daube_bridge.server
```

Or expose the HTTP MCP endpoint for remote/local integrations:

```bash
daube-bridge serve
# http://127.0.0.1:8000/mcp
```

## One-click MCPB

BRIDGE² ships an MCPB v0.4 bundle definition using the cross-platform `uv` runtime. Build the deterministic bundle with:

```bash
python scripts/build_mcpb.py
```

The build is reproducible: identical source produces an identical archive hash. Official MCP Registry metadata lives in [`server.json`](server.json).

## Target matrix

| Surface | Output | Strategy |
|---|---|---|
| MCP hosts | MCP server + tool schemas | Shared transport/tool backbone |
| OpenAI / ChatGPT / Codex | `SKILL.md`, MCP descriptor, function schemas | Skills + MCP/tool calling |
| Claude | `.claude-plugin/plugin.json`, `.mcp.json`, `SKILL.md` | Plugin + portable skill + MCP |
| Gemini / Google agents | `SKILL.md`, MCP config | Portable skill + MCP |
| DeepSeek | OpenAI-style `tools.json` | Function/tool calling adapter |
| Meta / Llama | neutral `tools.json` | Application/router function schema |
| Chromium browsers | Manifest V3 side panel | Endpoint/config control surface |

This matrix describes integration artifacts BRIDGE² generates. It does not invent provider capabilities that do not exist.

## Portable skill format

```yaml
name: My Research Skill
version: 0.1.0
description: Research and compare options.
tools:
  - name: compare_options
    description: Compare options against explicit criteria.
    parameters:
      type: object
      properties:
        options:
          type: array
          items: {type: string}
      required: [options]
```

## MCP tools

The bundled server exposes three small primitives:

- `bridge_targets` — discover supported compilation targets.
- `validate_skill` — validate a portable skill object.
- `compile_skill` — compile a skill in-memory for another agent or tool.

That makes BRIDGE² usable both as a CLI and as infrastructure callable by other agents.

## Verify before release

```bash
python scripts/verify.py
python scripts/build_mcpb.py
.tools/mcp-publisher.exe validate
```

The verification gate covers tests, Ruff, target discovery, sample compilation, wheel creation, deterministic MCPB creation, and official MCP Registry metadata validation.

## Roadmap

- ChatGPT Apps SDK interactive widget target.
- `npx` / TypeScript compiler parity.
- Provider capability detection and compatibility linting.
- Signed bundles and provenance manifests.
- Remote registry + searchable skill catalog.
- One-click adapters for agent IDEs and orchestration frameworks.
- Golden interoperability fixtures across providers.

## Project principles

1. **Portable by default.** Prefer MCP and open schemas over provider lock-in.
2. **Evidence over pretending.** Never claim native support that a provider does not have.
3. **Readable outputs.** Generated artifacts stay human-auditable and diffable.
4. **Safe boundaries.** Authentication and sensitive actions remain explicit.
5. **Fast adoption.** A useful first result should take minutes, not a framework migration.

## Contributing

Issues, adapters, compatibility fixtures, docs, and provider integrations are welcome. Provider-format changes should include a link to authoritative documentation and a minimal reproducible fixture.

Useful starting points:

- [`CONTRIBUTING.md`](CONTRIBUTING.md)
- [`docs/20K_STAR_PLAYBOOK.md`](docs/20K_STAR_PLAYBOOK.md)
- [`docs/CODEX_FOR_OSS.md`](docs/CODEX_FOR_OSS.md)
- [`docs/LAUNCH_KIT.md`](docs/LAUNCH_KIT.md)
- [`SECURITY.md`](SECURITY.md)

## License

MIT © 2026 D'AUBE SONNTAG.
