# Verification receipts

## v0.1.1

- Release tag commit: `a4a267917bd16ae28d58f9f6290d74df916dcd1b`
- Release payload commit: `8e4fd34bba35e93a58e16af91c13e00a914e7596`
- Python: `Python 3.13.15`
- Tests: `7 passed`
- Ruff: `All checks passed!`
- Targets: `7`
- Generated sample artifacts: `13`
- Wheel: `daube_agent_bridge-0.1.1-py3-none-any.whl`
- Wheel SHA256: `0e7056fc96c981b3c70ce2fffd23cf6b45421301b11fdeee392010957aec4778`
- MCPB: `daube-agent-bridge-0.1.1.mcpb`
- MCPB SHA256: `5073fb782d88a3dc8029218c457cb3c1741af1a593cbbcc15fb29d518fa952cc`
- MCP Registry validator: `server.json is valid`
- `git diff --check`: pass

Commands used:

```bash
python scripts/verify.py
python scripts/build_mcpb.py
.tools/mcp-publisher.exe validate
git diff --check
```

Verified locally on the maintainer workstation before the v0.1.1 tag.

## v0.1.0 historical receipt

- Base commit: `ca85cd302cb09aee4d1065ed4eb0f538c14f2bb4`
- Python: `Python 3.13.15`
- Tests: `6 passed`
- Ruff: `All checks passed!`
- Targets: `7`
- Generated sample artifacts: `13`
- Wheel: `daube_agent_bridge-0.1.0-py3-none-any.whl`
- Wheel SHA256: `dcbe0d6c7d5b49d6fb6bd40157ad127a578322291675dd5f0d319cd5bfe703f7`
