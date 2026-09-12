# D'AUBE // BRIDGEÂ²

> **Write once. Run across agents.**

D'AUBE // BRIDGEÂ² is an open-source universal AI skill compiler and MCP bridge. Define a capability once as a small YAML spec, then generate portable artifacts for ChatGPT/MCP, Claude, Gemini, DeepSeek, Meta/Llama, and browser-agent surfaces.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Why this exists

AI tooling is fragmented. The same capability is repeatedly rewritten as MCP tools, Claude skills/plugins, provider function schemas, browser extensions, and agent-specific configuration.

BRIDGEÂ² keeps the business logic provider-neutral and turns the integration layer into a compiler target.

```text
skill.yaml
   â”‚
   â”œâ”€â”€ MCP tool schema + endpoint config
   â”œâ”€â”€ Claude plugin + SKILL.md
   â”œâ”€â”€ Gemini SKILL.md + MCP config
   â”œâ”€â”€ DeepSeek OpenAI-style tools
   â”œâ”€â”€ Meta/Llama neutral function schema
   â””â”€â”€ Browser extension manifest
```

## Quick start

```bash
git clone https://github.com/daubesonntag-dotcom/daube-agent-bridge.git
cd daube-agent-bridge
python -m pip install -e ".[dev]"

daube-bridge validate examples/skill.yaml
daube-bridge compile examples/skill.yaml -o dist
daube-bridge serve
```

The MCP endpoint is then available at `http://127.0.0.1:8000/mcp`.

### Verify the entire release locally

```bash
python scripts/verify.py
```

That single command runs tests, Ruff, target discovery, sample compilation, wheel build, and prints the wheel SHA-256. See [`docs/VERIFICATION.md`](docs/VERIFICATION.md) for the v0.1.0 verification receipt.

## Target matrix

| Surface | v0.1 output | Strategy |
|---|---|---|
| OpenAI / ChatGPT / Codex | `SKILL.md`, MCP descriptor, function schemas | Native skills + MCP/tool calling |`n| MCP hosts | MCP server + tool schemas | Shared transport and tool backbone |
| Claude | `.claude-plugin/plugin.json`, `.mcp.json`, `SKILL.md` | Plugin + portable skill + MCP |
| Gemini / Google agents | `SKILL.md`, MCP config | Portable skill + remote/local MCP |
| DeepSeek | OpenAI-style `tools.json` | Function/tool calling adapter |
| Meta / Llama | neutral `tools.json` | Function schema for application/router layer |
| Chromium browsers | Manifest V3 side panel | Endpoint/config control surface |

This matrix describes generated integration artifacts, not extra capabilities invented by BRIDGEÂ².

## Skill format

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

The compiler validates the required fields and emits deterministic text artifacts across seven target families. The sample currently emits 13 artifacts. Generated files are designed to be readable, editable, diffable, and safe to commit.

## MCP tools

The included MCP server exposes three primitives:

- `bridge_targets` â€” discover supported targets.
- `validate_skill` â€” validate a portable skill object.
- `compile_skill` â€” compile a skill in-memory for another agent or tool.

That makes BRIDGEÂ² useful both as a CLI and as a tool that other agents can call.

## Browser side panel

Load `browser-extension/` as an unpacked Chromium extension to get a tiny BRIDGEÂ² control panel. It stores the MCP endpoint locally and generates the matching host configuration snippet.

## Roadmap

- ChatGPT Apps SDK interactive widget target.
- `npx` / TypeScript compiler parity.
- Provider capability detection and compatibility linting.
- Signed skill bundles and provenance manifests.
- Remote registry + searchable skill catalog.
- One-click adapters for agent IDEs and orchestration frameworks.
- Golden interoperability test suite across providers.

## Project principles

1. **Portable by default.** MCP and open schemas before provider lock-in.
2. **Evidence over pretending.** An adapter never claims native support that does not exist.
3. **Readable outputs.** Generated integration artifacts stay human-auditable.
4. **Safe boundaries.** Authentication and sensitive actions remain explicit.
5. **Fast adoption.** A useful first result should take minutes, not a framework migration.

## Contributing

Issues, adapters, compatibility fixtures, docs, and provider integrations are welcome. If a provider changes its tool or skill format, open an issue with a link to the authoritative documentation and a minimal reproducible fixture.

## Adoption and maintainer program

- [20K star operating target](docs/20K_STAR_PLAYBOOK.md)
- [Codex for Open Source readiness](docs/CODEX_FOR_OSS.md)
- [Launch kit](docs/LAUNCH_KIT.md)
- [Security policy](SECURITY.md)

## License

MIT Â© 2026 D'AUBE SONNTAG.

