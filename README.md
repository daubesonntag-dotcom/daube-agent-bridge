# D'AUBE // BRIDGE²

> **Write once. Run across agents.**

D'AUBE // BRIDGE² is an open-source universal AI skill compiler and MCP bridge. Define one portable capability spec, then compile it into integration artifacts for ChatGPT/Codex, Claude, Gemini, DeepSeek, Meta/Llama, MCP hosts, and Chromium browsers.

[![Release](https://img.shields.io/github/v/release/daubesonntag-dotcom/daube-agent-bridge)](https://github.com/daubesonntag-dotcom/daube-agent-bridge/releases)
[![MCP Registry](https://img.shields.io/badge/MCP%20Registry-active-brightgreen)](https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.daubesonntag-dotcom%2Fdaube-agent-bridge)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)

### External review

On 2026-09-18, the BRIDGE² deployment record was **AI Deploy Network Approved** after review of the submitted implementation evidence. This means the deployment record passed AI Deploy Network review; it is not a client-confirmed commercial outcome or a guarantee of production performance.

The canonical publication narrative is maintained in [`docs/AI_DEPLOY_CASE_STUDY.md`](docs/AI_DEPLOY_CASE_STUDY.md). The reviewed case study is now publicly available on [AI Deploy Network](https://aideploynetwork.com/case-studies/329c5ed8-4a7d-43b1-bb49-466827fd3330).

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

**Current release:** 7 target families, 15 deterministic artifacts, one MCP server.

## 30-second start

```bash
git clone https://github.com/daubesonntag-dotcom/daube-agent-bridge.git
cd daube-agent-bridge
python -m pip install -e ".[dev]"
daube-bridge validate examples/skill.yaml
daube-bridge compile examples/skill.yaml -o build/sample
```

Install the verified v0.1.3 wheel directly from GitHub Releases:

```bash
python -m pip install https://github.com/daubesonntag-dotcom/daube-agent-bridge/releases/download/v0.1.3/daube_agent_bridge-0.1.3-py3-none-any.whl
python -m daube_bridge doctor
```

`python -m daube_bridge ...` is the shim-free CLI path for Windows environments where Application Control blocks generated console-script executables.

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

After publishing a GitHub Release, smoke-test the public wheel in an isolated environment:

```bash
python scripts/smoke_release.py 0.1.3
```

## A2A cloud peer preflight (Draft POC)

BRIDGE² can now **prepare** a synthetic A2A 1.0 AgentCard handoff for review, with explicit HTTPS host, protocol binding, skill, classification and zero-spend boundaries. This is **not** live A2A transport, provider authentication or a claim of vendor API access. No network request is performed.

```bash
python -m daube_bridge.cloud_peer \
  --card examples/collaboration/agent-card.synthetic.json \
  --policy examples/collaboration/policy.synthetic.json \
  --request examples/collaboration/request.synthetic.json
PYTHONPATH=src pytest -q tests/test_cloud_peer.py
```

The synthetic peer uses the reserved domain `example.com`, not an actual AI provider. Remote answers are **untrusted** until reviewed; no consumer may execute embedded instructions. See [cloud peer review](docs/CLOUD_PEER_REVIEW_2026_10_13.md) for limitations, supported A2A 1.0 card fields and the separate approval path required before connecting a real cloud agent.


### Public Agent Card inspection (no remote task)

BRIDGE² can check a previously fetched public A2A card with a strict reviewed allowlist and zero-spend, network-disabled policy. This accepts A2A 1.0 peers advertising a JSON-only output mode, but the inspection alone neither authenticates nor executes any peer.

~~~bash
python -m daube_bridge.cloud_peer \
  --card PUBLIC_CARD_FROM_AUTHORIZED_FETCH.json \
  --policy REVIEWED_OFFLINE_POLICY.json \
  --inspect-only \
  --source-url https://agent.example.com/.well-known/agent-card.json
~~~

A separate public metadata fetch of AgentCard.net returned HTTP 200 / application/a2a+json through a connected cloud research service on 2026-10-13; **no task was sent**. [Provenance, limits and review findings](docs/CLOUD_PEER_REVIEW_2026_10_13.md).

### Review raw Agent Card fetch bytes (Draft/HOLD)

For an authorized **public-only** fetch captured by another cloud tool, BRIDGE² can check the exact saved JSON bytes, status/MIME/redirect metadata, allowed host, and changed SHA-256 **without itself accessing the network**:

```bash
python -m daube_bridge.cloud_peer \
  --card examples/collaboration/agent-card.synthetic.json \
  --policy examples/collaboration/policy.synthetic.json \
  --inspect-fetched-card \
  --source-url https://agent.example.com/.well-known/agent-card.json \
  --http-status 200 --content-type application/a2a+json --redirect-count 0
```

The example contains fictional metadata and a **fictional HTTP status**; the CLI does not authenticate the reporter or the origin. All outputs retain `source_fetch_verified=false`, `identity_verified=false` and `external_action_authorized=false`. To detect drift, optionally add `--previous-sha256` with the prior raw digest.

One separate public, no-credential, **synthetic-only** AgentCard.net validation API canary returned HTTP 200 and `validation.valid=true` through a connected cloud research tool; it did **not** run within BRIDGE² code or invoke a general-purpose LLM. Evidence, limits and exact tests: [Public discovery receipt review](docs/DISCOVERY_RECEIPT_INTEGRATION_20261013.md). No paid or private data access is implied.

### Optional A2A Python SDK contract (draft, no network)

The read-only [A2A SDK adapter](src/daube_bridge/a2a_sdk_adapter.py) can prepare an official v1.2.2 `SendMessageRequest` and non-streaming `ClientConfig` from an already-vetted synthetic BRIDGE² handoff. It **does not instantiate a client, make an HTTP request, obtain credentials or grant permission**. The base BRIDGE² compiler does not require an A2A SDK dependency.

```bash
PYTHONPATH=src python -m daube_bridge.a2a_sdk_adapter \
  --card examples/collaboration/agent-card.synthetic.json \
  --request examples/collaboration/request.synthetic.json \
  --policy examples/collaboration/policy.synthetic.json

# Only after optional dependency admission, run the actual offline SDK contract:
python -m pip install -e '.[a2a]'
PYTHONPATH=src python scripts/verify_a2a_sdk_contract.py
```

The CLI plan redacts raw task text and raw request IDs, uses hashes for audit correlation, and reports `SDK_PREPARED_NO_NETWORK` with `external_action_authorized=false`. Installing `a2a-sdk==1.2.2` is opt-in. See [provenance, QA and release constraints](docs/A2A_SDK_OFFLINE_ADMISSION_20261013.md). Real remote agent transport needs its own verified identity, consent, authorization, budget and exact-HEAD release gates.

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
- [`CHANGELOG.md`](CHANGELOG.md)
- [`GOVERNANCE.md`](GOVERNANCE.md)
- [`docs/PROVIDER_COMPATIBILITY.md`](docs/PROVIDER_COMPATIBILITY.md)
- [`docs/20K_STAR_PLAYBOOK.md`](docs/20K_STAR_PLAYBOOK.md)
- [`docs/CODEX_FOR_OSS.md`](docs/CODEX_FOR_OSS.md)
- [`docs/OPEN_SOURCE_FUND.md`](docs/OPEN_SOURCE_FUND.md)
- [`docs/DISTRIBUTION.md`](docs/DISTRIBUTION.md)
- [`docs/PERFORMANCE_EVIDENCE.md`](docs/PERFORMANCE_EVIDENCE.md)
- [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md)
- [`docs/AI_DEPLOY_NETWORK.md`](docs/AI_DEPLOY_NETWORK.md)
- [`docs/LAUNCH_KIT.md`](docs/LAUNCH_KIT.md)
- [`SECURITY.md`](SECURITY.md)

## License

MIT © 2026 D'AUBE SONNTAG.
