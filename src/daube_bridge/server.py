from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from .compiler import TARGETS, compile_spec
from .model import SkillSpec

mcp = FastMCP(
    "D'AUBE // BRIDGE2",
    instructions=(
        "Universal AI skill compiler. Validate a portable skill spec and compile "
        "it into MCP, Claude, Gemini, DeepSeek, Meta and browser artifacts."
    ),
)


@mcp.tool
def bridge_targets() -> dict[str, Any]:
    """Return supported compilation targets and the bridge version."""
    return {"targets": list(TARGETS), "version": "0.1.1"}


@mcp.tool
def validate_skill(spec: dict[str, Any]) -> dict[str, Any]:
    """Validate a portable D'AUBE skill specification."""
    parsed = SkillSpec.from_dict(spec)
    return {"valid": True, "name": parsed.name, "tools": len(parsed.tools)}


@mcp.tool
def compile_skill(
    spec: dict[str, Any], endpoint: str = "http://localhost:8000/mcp"
) -> dict[str, str]:
    """Compile one skill spec into artifacts for supported AI surfaces."""
    parsed = SkillSpec.from_dict(spec)
    return compile_spec(parsed, endpoint=endpoint)


if __name__ == "__main__":
    mcp.run()
