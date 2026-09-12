# Verification receipts

## v0.1.3

- Release payload commit: `58711180fca5a7092dca833a1db761e283526b6d`
- Python: `Python 3.13.15`
- Tests: `15 passed`
- Ruff: `All checks passed!`
- Targets: `7`
- Generated sample artifacts: `15`
- Wheel: `daube_agent_bridge-0.1.3-py3-none-any.whl`
- Wheel SHA256: `11ee2556c895b6c9900ad2ec7d8ee786f49caca51373618be3df2c81ccf878b0`
- MCPB: `daube-agent-bridge-0.1.3.mcpb`
- MCPB SHA256: `bb50805481f287605db958c1e6de3cee94a6c5dd90df44bb37b59f95ddfb991a`
- MCP Registry validator: `server.json is valid`
- Public/runtime smoke: isolated wheel `python -m daube_bridge doctor` pass
- `git diff --check`: pass

## v0.1.2

- Release payload commit: `9b701c285e9e5ba0e4ef2b86c582271d0c296d09`
- Python: `Python 3.13.15`
- Tests: `10 passed`
- Ruff: `All checks passed!`
- Targets: `7`
- Generated sample artifacts: `13`
- Wheel: `daube_agent_bridge-0.1.2-py3-none-any.whl`
- Wheel SHA256: `86497d9848ee8bdb11f3213f318569d14ce6806e120d53bcd847365d9ec3f0f9`
- MCPB: `daube-agent-bridge-0.1.2.mcpb`
- MCPB SHA256: `de8a5157fce9ee27ca5d88f33389f68f99cf8cf6d83b00eeaff3d35aeb8a9508`
- MCP Registry validator: `server.json is valid`
- Isolated wheel runtime: `python -m daube_bridge doctor` passed
- Wheel contains `daube_bridge/__main__.py`
- Registry title Unicode regression: U+00B2 verified
- `git diff --check`: pass

Verified locally before the v0.1.2 tag. The verifier is source-local and does not depend on another editable checkout.

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
