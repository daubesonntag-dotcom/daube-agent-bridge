from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlsplit

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from .compiler import TARGETS, compile_spec
from .model import SkillSpec

MAX_ENDPOINT_CHARS = 2_048
MAX_COMPILED_OUTPUT_BYTES = 1_048_576

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


def _validate_endpoint(endpoint: str) -> str:
    if not isinstance(endpoint, str):
        raise ValueError("endpoint must be a string")
    if not endpoint or endpoint != endpoint.strip():
        raise ValueError("endpoint must be non-empty and contain no surrounding whitespace")
    if len(endpoint) > MAX_ENDPOINT_CHARS:
        raise ValueError(f"endpoint exceeds {MAX_ENDPOINT_CHARS} characters")
    if any(character.isspace() for character in endpoint):
        raise ValueError("endpoint must not contain whitespace")

    parsed = urlsplit(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("endpoint must be an absolute http(s) URL")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("endpoint must not contain embedded credentials")
    try:
        parsed.port
    except ValueError as exc:
        raise ValueError("endpoint contains an invalid port") from exc
    return endpoint


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
    """Compile a skill in memory; the endpoint is validated and never contacted."""
    parsed = SkillSpec.from_dict(spec)
    safe_endpoint = _validate_endpoint(endpoint)
    artifacts = compile_spec(parsed, endpoint=safe_endpoint)
    output_bytes = sum(len(value.encode("utf-8")) for value in artifacts.values())
    if output_bytes > MAX_COMPILED_OUTPUT_BYTES:
        raise ValueError(
            f"compiled output exceeds {MAX_COMPILED_OUTPUT_BYTES} bytes"
        )
    return artifacts


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
