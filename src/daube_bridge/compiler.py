[Reading 170 lines from start (total: 170 lines, 0 remaining)]

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

from .model import SkillSpec

TARGETS = (
    "mcp",
    "openai",
    "claude",
    "gemini",
    "deepseek",
    "meta",
    "browser",
)


def slugify(value: str) -> str:
    """Create a portable lowercase identifier for every target ecosystem."""
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        raise ValueError("Skill name must contain at least one ASCII letter or digit")
    return slug


def load_spec(path: str | Path) -> SkillSpec:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError("Skill spec root must be a mapping")
    return SkillSpec.from_dict(raw)


def tool_schema(spec: SkillSpec) -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"],
            },
        }
        for tool in spec.tools
    ]


def _skill_markdown(spec: SkillSpec, slug: str) -> str:
    sections = [
        f"---\nname: {slug}\ndescription: {spec.description}\n---\n",
        f"# {spec.name}\n\n{spec.description}\n",
    ]
    if spec.required_capabilities:
        sections.append(
            "## Required capabilities\n\n"
            + "\n".join(f"- {capability}" for capability in spec.required_capabilities)
            + "\n"
        )
    governance: list[str] = []
    if spec.authority_class:
        governance.append(f"Authority class: `{spec.authority_class}`")
    if spec.required_evidence:
        governance.append("Required evidence: " + ", ".join(spec.required_evidence))
    if spec.data_classes:
        governance.append("Data classes: " + ", ".join(spec.data_classes))
    if spec.cost_policy:
        governance.append(
            "Cost policy: "
            f"{spec.cost_policy['cost_class']} / ceiling={spec.cost_policy['cost_ceiling']}"
        )
    if spec.domain_dependencies:
        governance.append("Domain dependencies: " + ", ".join(spec.domain_dependencies))
    if governance:
        sections.append("## Governance\n\n" + "\n".join(f"- {item}" for item in governance) + "\n")
    if spec.instructions:
        sections.append(
            "## Operating instructions\n\n"
            + "\n".join(f"{index}. {instruction}" for index, instruction in enumerate(spec.instructions, 1))
            + "\n"
        )
    sections.append("Use the D'AUBE Bridge MCP server when these capabilities are relevant.\n")
    return "\n".join(sections)


def compile_spec(
    spec: SkillSpec,
    endpoint: str = "http://localhost:8000/mcp",
) -> dict[str, str]:
    slug = slugify(spec.name)
    gemini_name = slug.replace("-", "_")
    tools = tool_schema(spec)
    skill_md = _skill_markdown(spec, slug)
    claude_plugin = {
        "name": slug,
        "version": spec.version,
        "description": spec.description,
        "author": {"name": "D'AUBE SONNTAG"},
    }
    mcp_config = {"mcpServers": {slug: {"type": "http", "url": endpoint}}}
    openai_mcp = {
        "type": "mcp",
        "server_label": slug,
        "server_url": endpoint,
    }
    gemini_mcp = {
        "type": "mcp_server",
        "name": gemini_name,
        "url": endpoint,
    }
    browser_manifest = {
        "manifest_version": 3,
        "name": f"{spec.name} — D'AUBE Bridge",
        "version": spec.version,
        "description": spec.description,
        "permissions": ["storage", "sidePanel"],
        "side_panel": {"default_path": "sidepanel.html"},
    }
    neutral_tools = [item["function"] for item in tools]
    bridge_manifest = {
        "schema": "https://daubesonntag.com/bridge/v1",
        "name": spec.name,
        "slug": slug,
        "version": spec.version,
        "description": spec.description,
        "endpoint": endpoint,
        "targets": list(TARGETS),
        "required_capabilities": spec.required_capabilities,
        "authority_class": spec.authority_class,
        "required_evidence": spec.required_evidence,
        "data_classes": spec.data_classes,
        "cost_policy": spec.cost_policy,
        "domain_dependencies": spec.domain_dependencies,
        "instructions": spec.instructions,
        "tools": neutral_tools,
    }
    pretty = lambda value: json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    return {
        "bridge/manifest.json": pretty(bridge_manifest),
        "mcp/tools.json": pretty(tools),
        "openai/SKILL.md": skill_md,
        "openai/mcp-tool.json": pretty(openai_mcp),
        "openai/functions.json": pretty(tools),
        "claude/.claude-plugin/plugin.json": pretty(claude_plugin),
        "claude/.mcp.json": pretty(mcp_config),
        f"claude/skills/{slug}/SKILL.md": skill_md,
        "gemini/SKILL.md": skill_md,
        "gemini/mcp.json": pretty(mcp_config),
        f"gemini/.agents/skills/{slug}/SKILL.md": skill_md,
        "gemini/mcp-tool.json": pretty(gemini_mcp),
        "deepseek/tools.json": pretty(tools),
        "meta/tools.json": pretty(neutral_tools),
        "browser/manifest.json": pretty(browser_manifest),
    }


def write_artifacts(
    artifacts: dict[str, str], out_dir: str | Path
) -> list[Path]:
    root = Path(out_dir)
    written: list[Path] = []
    for relative, content in artifacts.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written

[executed on device: daube-host-01.us-central1-a.c.disco-rope-507506-f7.internal (18782d8a-e52d-40f0-84d8-f4bc86787e89)]