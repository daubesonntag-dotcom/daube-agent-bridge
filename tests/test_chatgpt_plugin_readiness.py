from __future__ import annotations

import asyncio

from fastmcp import Client

from daube_bridge.server import mcp


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
