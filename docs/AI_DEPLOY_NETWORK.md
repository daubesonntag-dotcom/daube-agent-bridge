# AI Deploy Network submission brief

This document is the canonical, evidence-first description of D'AUBE // BRIDGE² for portfolio and deployment-review workflows.

## Deployment title

**D'AUBE // BRIDGE² — Universal AI Skill Compiler & MCP Bridge**

## Builder

**D'AUBE SONNTAG**

## Deployment class

Use the closest available platform category to:

- AI Infrastructure
- Developer Tools
- AI Agents / Agent Infrastructure
- Systems Integration
- MCP / Tooling

Do not label the project as a client deployment unless a real client engagement can be evidenced.

## Status wording

Preferred:

**Public open-source release with an active Official MCP Registry record.**

Avoid unsupported wording such as "enterprise production deployment", "industry-leading", "mission-critical", "99.99% uptime", or any client/business outcome that has not been independently evidenced.

## One-line summary

BRIDGE² lets developers define one portable AI capability specification and compile it into auditable integration artifacts for MCP, OpenAI/ChatGPT/Codex, Claude, Gemini, DeepSeek, Meta/Llama and Chromium-based agent surfaces.

## Challenge

Agent ecosystems expose overlapping capabilities through different skill, plugin, function-tool, MCP and browser integration formats. Maintaining the same capability separately for each surface creates duplicated work, compatibility drift and a larger verification burden.

## Solution delivered

BRIDGE² treats provider and host formats as compiler targets while keeping the capability definition provider-neutral.

A single portable YAML skill specification can be validated and compiled into:

- MCP tool schemas and server integration;
- OpenAI / ChatGPT / Codex skill, MCP and function-tool artifacts;
- Claude plugin, MCP and skill artifacts;
- Gemini skill and MCP artifacts;
- DeepSeek tool schemas;
- Meta/Llama neutral function schemas;
- Chromium Manifest V3 integration metadata.

Generated output is readable and diffable. The project intentionally avoids inventing provider capabilities that do not exist.

## Current verified technical record

For release v0.1.3, the repository records:

- 7 target families;
- 15 deterministic generated artifacts;
- 15 passing tests;
- Ruff checks passing;
- deterministic MCPB build;
- release wheel with published SHA256;
- MCPB archive with published SHA256;
- valid Official MCP Registry metadata;
- isolated public-wheel runtime smoke test passing;
- `git diff --check` passing.

These are technical verification facts. They are not client-confirmed business outcomes.

## Technologies

Use only technologies actually represented in the release:

- Python 3.11+
- FastMCP
- Model Context Protocol (MCP)
- YAML
- JSON / JSON-style function schemas
- MCPB
- Chromium Manifest V3
- Git / GitHub
- pytest
- Ruff

Provider integration targets represented by generated artifacts include OpenAI/ChatGPT/Codex, Claude, Gemini, DeepSeek and Meta/Llama.

Do not present a target provider as a partnership, certification or endorsement.

## Evidence links

Repository:

https://github.com/daubesonntag-dotcom/daube-agent-bridge

Release:

https://github.com/daubesonntag-dotcom/daube-agent-bridge/releases/tag/v0.1.3

Verification receipts:

https://github.com/daubesonntag-dotcom/daube-agent-bridge/blob/main/docs/VERIFICATION.md

Provider compatibility:

https://github.com/daubesonntag-dotcom/daube-agent-bridge/blob/main/docs/PROVIDER_COMPATIBILITY.md

Security policy:

https://github.com/daubesonntag-dotcom/daube-agent-bridge/blob/main/SECURITY.md

Threat model:

https://github.com/daubesonntag-dotcom/daube-agent-bridge/blob/main/docs/THREAT_MODEL.md

Performance evidence methodology:

https://github.com/daubesonntag-dotcom/daube-agent-bridge/blob/main/docs/PERFORMANCE_EVIDENCE.md

Official MCP Registry identifier:

`io.github.daubesonntag-dotcom/daube-agent-bridge`

## Release evidence

v0.1.3 release payload commit:

`58711180fca5a7092dca833a1db761e283526b6d`

Wheel:

`daube_agent_bridge-0.1.3-py3-none-any.whl`

Wheel SHA256:

`11ee2556c895b6c9900ad2ec7d8ee786f49caca51373618be3df2c81ccf878b0`

MCPB:

`daube-agent-bridge-0.1.3.mcpb`

MCPB SHA256:

`bb50805481f287605db958c1e6de3cee94a6c5dd90df44bb37b59f95ddfb991a`

## Measurable outcomes field

Until there is a real organisation engagement with independently evidenced impact, do **not** fabricate hours saved, cost saved, revenue impact or adoption.

If the platform allows a technical-results section, use:

**Technical result:** one portable skill definition compiles into 15 auditable artifacts spanning 7 target families in v0.1.3, with release verification receipts and deterministic package hashes.

If the platform specifically asks for business outcomes, use:

**No client-confirmed business outcome submitted yet. Public technical evidence is attached separately.**

## Verification request note

Suggested reviewer note:

> BRIDGE² is a public MIT-licensed interoperability project maintained by D'AUBE SONNTAG. The submission is intentionally limited to claims that can be inspected in the public repository, release receipts and Official MCP Registry record. Release v0.1.3 includes reproducible verification receipts, deterministic package hashes, provider-compatibility fixtures and an isolated wheel smoke test. No client-confirmed business outcome is claimed.

## Case-study structure after deployment approval

### Situation

AI integration work is fragmented across provider-specific skill, tool, plugin and MCP formats.

### Approach

Create a small provider-neutral capability specification and compile that semantic definition into explicit, inspectable target artifacts.

### Key decisions

- provider-neutral semantic source;
- text-first, human-auditable generated output;
- MCP as a shared interoperability surface;
- compatibility claims tied to authoritative provider behavior;
- deterministic packaging and release receipts;
- explicit security boundaries rather than hidden credentials or automatic privilege.

### Result

A public v0.1.3 release that generates 15 artifacts across 7 target families and is listed in the Official MCP Registry, with test/lint/build/smoke verification recorded in the repository.

### Lessons

- interoperability claims need fixtures, not marketing language;
- deterministic build evidence is more useful than unsupported performance adjectives;
- provider capability drift should be treated as a compatibility-maintenance problem;
- technical metrics and business outcomes must remain clearly separated.

### Future improvements

- signed provenance and release attestations;
- package/install telemetry beyond release-asset counts;
- historical benchmark receipts;
- stricter schema hardening and fuzz/property testing;
- external downstream integrations and non-maintainer contributions;
- client-confirmed business outcomes when a real implementation engagement exists.
