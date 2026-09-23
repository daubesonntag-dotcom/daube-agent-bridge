from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

MAX_SPEC_BYTES = 262_144
MAX_TOOLS = 64
MAX_SCHEMA_DEPTH = 16
MAX_SCHEMA_NODES = 4_096
MAX_SKILL_NAME = 128
MAX_VERSION = 64
MAX_DESCRIPTION = 4_096
MAX_INSTRUCTIONS = 64
MAX_REQUIRED_CAPABILITIES = 64
PORTABLE_TOOL_NAME = re.compile(r"^[A-Za-z0-9_-]+$")
PORTABLE_CAPABILITY = re.compile(r"^[A-Za-z0-9_.:/-]+$")


def _bounded_text(value: Any, field_name: str, limit: int) -> str:
    text = str(value)
    if not text.strip():
        raise ValueError(f"{field_name} must not be empty")
    if len(text) > limit:
        raise ValueError(f"{field_name} exceeds {limit} characters")
    return text


def _validate_schema_tree(value: Any, *, depth: int = 0, counter: list[int] | None = None) -> None:
    if counter is None:
        counter = [0]

    counter[0] += 1
    if counter[0] > MAX_SCHEMA_NODES:
        raise ValueError(f"parameter schema exceeds {MAX_SCHEMA_NODES} nodes")
    if depth > MAX_SCHEMA_DEPTH:
        raise ValueError(f"parameter schema exceeds depth {MAX_SCHEMA_DEPTH}")

    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ValueError("parameter schema keys must be strings")
            _validate_schema_tree(child, depth=depth + 1, counter=counter)
    elif isinstance(value, list):
        for child in value:
            _validate_schema_tree(child, depth=depth + 1, counter=counter)
    elif value is not None and not isinstance(value, (str, int, float, bool)):
        raise ValueError("parameter schema must contain JSON-compatible values")


def _string_list(
    raw: Any,
    field_name: str,
    *,
    max_items: int,
    item_limit: int,
    pattern: re.Pattern[str] | None = None,
) -> list[str]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError(f"{field_name} must be a list")
    if len(raw) > max_items:
        raise ValueError(f"{field_name} exceeds maximum of {max_items}")
    values: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(raw):
        value = _bounded_text(item, f"{field_name}[{index}]", item_limit).strip()
        if pattern is not None and not pattern.fullmatch(value):
            raise ValueError(f"{field_name}[{index}] is not portable")
        if value not in seen:
            seen.add(value)
            values.append(value)
    return values


@dataclass(slots=True)
class SkillSpec:
    name: str
    description: str
    version: str
    tools: list[dict[str, Any]]
    instructions: list[str] = field(default_factory=list)
    required_capabilities: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> SkillSpec:
        if not isinstance(raw, dict):
            raise TypeError("Skill spec root must be a mapping")

        try:
            encoded = json.dumps(raw, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise ValueError("Skill spec must be JSON-serializable") from exc
        if len(encoded) > MAX_SPEC_BYTES:
            raise ValueError(f"Skill spec exceeds {MAX_SPEC_BYTES} bytes")

        required = ("name", "description", "version", "tools")
        missing = [key for key in required if key not in raw]
        if missing:
            raise ValueError(f"Missing required keys: {', '.join(missing)}")

        name = _bounded_text(raw["name"], "name", MAX_SKILL_NAME)
        description = _bounded_text(raw["description"], "description", MAX_DESCRIPTION)
        version = _bounded_text(raw["version"], "version", MAX_VERSION)
        instructions = _string_list(
            raw.get("instructions"),
            "instructions",
            max_items=MAX_INSTRUCTIONS,
            item_limit=MAX_DESCRIPTION,
        )
        required_capabilities = _string_list(
            raw.get("required_capabilities"),
            "required_capabilities",
            max_items=MAX_REQUIRED_CAPABILITIES,
            item_limit=128,
            pattern=PORTABLE_CAPABILITY,
        )

        raw_tools = raw["tools"]
        if not isinstance(raw_tools, list) or not raw_tools:
            raise ValueError("tools must be a non-empty list")
        if len(raw_tools) > MAX_TOOLS:
            raise ValueError(f"tools exceeds maximum of {MAX_TOOLS}")

        tools: list[dict[str, Any]] = []
        names: set[str] = set()

        for index, raw_tool in enumerate(raw_tools):
            if not isinstance(raw_tool, dict):
                raise ValueError(f"tool[{index}] must be an object")
            if "name" not in raw_tool or "description" not in raw_tool:
                raise ValueError(f"tool[{index}] needs name and description")

            tool_name = _bounded_text(raw_tool["name"], f"tool[{index}].name", MAX_TOOL_NAME)
            if not PORTABLE_TOOL_NAME.fullmatch(tool_name):
                raise ValueError(
                    f"tool[{index}].name must match {PORTABLE_TOOL_NAME.pattern}"
                )
            if tool_name in names:
                raise ValueError(f"Duplicate tool name: {tool_name}")
            names.add(tool_name)

            tool_description = _bounded_text(
                raw_tool["description"],
                f"tool[{index}].description",
                MAX_DESCRIPTION,
            )

            parameters = raw_tool.get("parameters", {"type": "object", "properties": {}})
            if not isinstance(parameters, dict):
                raise ValueError(f"tool[{index}].parameters must be an object")
            if parameters.get("type", "object") != "object":
                raise ValueError(f"tool[{index}].parameters.type must be object")
            properties = parameters.get("properties", {})
            if not isinstance(properties, dict):
                raise ValueError(f"tool[{index}].parameters.properties must be an object")
            required_fields = parameters.get("required", [])
            if not isinstance(required_fields, list) or not all(
                isinstance(item, str) for item in required_fields
            ):
                raise ValueError(f"tool[{index}].parameters.required must be a string list")
            _validate_schema_tree(parameters)

            tool = dict(raw_tool)
            tool["name"] = tool_name
            tool["description"] = tool_description
            tool["parameters"] = parameters
            tools.append(tool)

        return cls(
            name=name,
            description=description,
            version=version,
            tools=tools,
            instructions=instructions,
            required_capabilities=required_capabilities,
        )
