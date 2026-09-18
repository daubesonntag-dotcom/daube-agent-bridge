from __future__ import annotations

import os
from typing import Any

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from .compiler import TARGETS, compile_spec
from .model import SkillSpec

mcp = FastMCP(
    "D'AUBE // BRIDGE2",
    instructions=(
        "Universal AI skill compiler. Validate a portable skill spec and compile "
        "it into MCP, Claude, Gemini, DeepSeek, Meta and browser artifacts."
    ),
)


READ_ONLY_CLOSED_WORLD = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)


@mcp.tool(
    title="List BRIDGE² targets",
    annotations=READ_ONLY_CLOSED_WORLD,
)
def bridge_targets() -> dict[str, Any]:
    """List supported compilation targets and the current bridge version."""
    return {"targets": list(TARGETS), "version": "0.1.3"}


@mcp.tool(
    title="Validate portable skill",
    annotations=READ_ONLY_CLOSED_WORLD,
)
def validate_skill(spec: dict[str, Any]) -> dict[str, Any]:
    """Validate a portable D'AUBE skill specification without persisting it."""
    parsed = SkillSpec.from_dict(spec)
    return {"valid": True, "name": parsed.name, "tools": len(parsed.tools)}


@mcp.tool(
    title="Compile portable skill",
    annotations=READ_ONLY_CLOSED_WORLD,
)
def compile_skill(
    spec: dict[str, Any], endpoint: str = "http://localhost:8000/mcp"
) -> dict[str, str]:
    """Compile a skill in memory; the endpoint string is embedded, not contacted."""
    parsed = SkillSpec.from_dict(spec)
    return compile_spec(parsed, endpoint=endpoint)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    """Unauthenticated liveness endpoint for hosting and review scanners."""
    return PlainTextResponse("ok")


@mcp.custom_route("/.well-known/openai-apps-challenge", methods=["GET"])
async def openai_apps_challenge(request: Request) -> PlainTextResponse:
    """Serve the exact OpenAI domain-verification token when configured."""
    token = os.getenv("OPENAI_APPS_CHALLENGE", "")
    if not token:
        return PlainTextResponse("challenge token not configured", status_code=404)
    return PlainTextResponse(token)


if __name__ == "__main__":
    mcp.run()
