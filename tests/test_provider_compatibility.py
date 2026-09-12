from __future__ import annotations

import json

from daube_bridge.compiler import compile_spec
from tests.test_compiler import sample


def test_openai_remote_mcp_descriptor_matches_current_shape():
    data = json.loads(compile_spec(sample())["openai/mcp-tool.json"])
    assert data == {
        "type": "mcp",
        "server_label": "demo-skill",
        "server_url": "http://localhost:8000/mcp",
    }


def test_claude_project_mcp_config_stays_portable():
    data = json.loads(compile_spec(sample())["claude/.mcp.json"])
    server = data["mcpServers"]["demo-skill"]
    assert server == {"type": "http", "url": "http://localhost:8000/mcp"}


def test_gemini_emits_current_remote_mcp_and_skill_paths():
    artifacts = compile_spec(sample())
    tool = json.loads(artifacts["gemini/mcp-tool.json"])
    assert tool == {
        "type": "mcp_server",
        "name": "demo_skill",
        "url": "http://localhost:8000/mcp",
    }
    assert "gemini/.agents/skills/demo-skill/SKILL.md" in artifacts
