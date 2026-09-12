# BRIDGE² Launch Kit

## One-line pitch
Write one AI skill spec. Compile it for ChatGPT/Codex, MCP, Claude, Gemini, DeepSeek, Meta/Llama, and browser surfaces.

## GitHub description
Universal AI skill compiler + MCP bridge. Write once, generate portable artifacts for ChatGPT/Codex, Claude, Gemini, DeepSeek, Meta/Llama and browsers.

## Hacker News
**Title:** Show HN: BRIDGE² – write one AI skill spec, compile it for multiple agents

I built BRIDGE² because every agent ecosystem keeps asking developers to rewrite the same capability as a slightly different skill, plugin, MCP config, or function schema. BRIDGE² takes a small YAML skill definition and emits auditable artifacts for OpenAI/ChatGPT/Codex, Claude, Gemini, DeepSeek, Meta/Llama, MCP hosts, and browser surfaces. The core is intentionally provider-neutral and the generated output is readable text, so you can diff or edit it instead of trusting a black box. MIT licensed. I’d especially value feedback on provider compatibility and formats worth adding next.

## Reddit / developer communities
If you maintain the same tools across multiple AI agents, I’d love feedback on BRIDGE². It compiles one portable YAML skill into provider-specific integration artifacts while keeping MCP as the shared backbone. The first release targets OpenAI/ChatGPT/Codex, Claude, Gemini, DeepSeek, Meta/Llama, MCP hosts, and Chromium surfaces. I’m looking for real compatibility gaps, not vanity integrations—links to authoritative provider docs are especially useful.

## X / Threads
AI agent integrations are fragmenting fast. BRIDGE² takes one portable skill spec and compiles it into artifacts for ChatGPT/Codex, MCP, Claude, Gemini, DeepSeek, Meta/Llama and browser surfaces. Open source, MIT, human-auditable outputs. Write once. Run across agents.

## LinkedIn
Today I’m open-sourcing D’AUBE // BRIDGE², a universal AI skill compiler and MCP bridge. The problem is simple: teams increasingly maintain the same capability several times because each agent ecosystem has its own skill, plugin, MCP, or function-tool format. BRIDGE² keeps the capability definition provider-neutral, then generates readable integration artifacts for major agent surfaces. The project is early and deliberately evidence-driven: adapters should correspond to real provider capabilities, and compatibility changes should be backed by authoritative documentation and fixtures. Contributions and provider-format feedback are welcome.

## Demo script
1. Show a 20-line `skill.yaml`.
2. Run `daube-bridge validate`.
3. Run `daube-bridge compile`.
4. Fan out the generated folders on screen.
5. Open the OpenAI, Claude, Gemini, DeepSeek and Meta outputs side by side.
6. End on: **Write once. Run across agents.**
