from __future__ import annotations

import asyncio

import pytest
from fastmcp import Client

from daube_bridge.server import MAX_COMPILED_OUTPUT_BYTES, _validate_endpoint, compile_skill, mcp


def test_chatgpt_review_annotations_are_explicit() -> None:
    async def run() -> None:
        async with Client(mcp) as client:
            tools = await client.list_tools()

        by_name = {tool.name: tool for tool in tools}
        assert set(by_name) == {"bridge_targets", "validate_skill", "compile_skill"}

        for tool in by_name.values():
            assert tool.annotations is not None
            assert tool.annotations.readOnlyHint is True
            assert tool.annotations.destructiveHint is False
            assert tool.annotations.openWorldHint is False
            assert tool.annotations.idempotentHint is True
            assert tool.title

    asyncio.run(run())


def test_endpoint_validation_rejects_unsafe_or_unbounded_values() -> None:
    assert _validate_endpoint("http://localhost:8000/mcp") == "http://localhost:8000/mcp"
    assert _validate_endpoint("https://example.com/mcp?mode=review") == "https://example.com/mcp?mode=review"

    for endpoint in (
        "ftp://example.com/mcp",
        " https://example.com/mcp",
        "https://user:secret@example.com/mcp",
        "https://example.com:99999/mcp",
        "https://exa mple.com/mcp",
        "https://" + ("a" * 2050) + ".example/mcp",
    ):
        with pytest.raises(ValueError):
            _validate_endpoint(endpoint)


def test_compile_skill_rejects_excessive_generated_output() -> None:
    tools = [
        {
            "name": f"tool_{index}",
            "description": "x" * 3300,
            "parameters": {"type": "object", "properties": {}},
        }
        for index in range(64)
    ]
    spec = {
        "name": "Large but valid skill",
        "description": "Output expansion guard",
        "version": "0.1.0",
        "tools": tools,
    }

    with pytest.raises(ValueError, match=f"compiled output exceeds {MAX_COMPILED_OUTPUT_BYTES} bytes"):
        compile_skill(spec)
