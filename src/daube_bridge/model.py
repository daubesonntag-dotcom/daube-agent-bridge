[Reading 242 lines from start (total: 242 lines, 0 remaining)]

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
MAX_TOOL_NAME = 64
MAX_INSTRUCTIONS = 64
MAX_REQUIRED_CAPABILITIES = 64
MAX_REQUIRED_EVIDENCE = 64
MAX_DATA_CLASSES = 16
MAX_DOMAIN_DEPENDENCIES = 64
PORTABLE_TOOL_NAME = re.compile(r"^[A-Za-z0-9_-]+$")
PORTABLE_CAPABILITY = re.compile(r"^[A-Za-z0-9_.:/-]+$")
PORTABLE_DOMAIN_DEPENDENCY = re.compile(r"^[A-Za-z0-9_.:/-]+(?:@[A-Za-z0-9_.-]+)?$")
AUTHORITY_CLASSES = frozenset({"AUTO_A", "AUTO_B", "GATED_C", "HOLD_D"})
DATA_CLASSES = frozenset({"public", "internal", "private", "sensitive", "regulated"})
COST_CLASSES = frozenset({"free", "metered", "paid", "unknown"})


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
    authority_class: str | None = None
    required_evidence: list[str] = field(default_factory=list)
    data_classes: list[str] = field(default_factory=list)
    cost_policy: dict[str, Any] | None = None
    domain_dependencies: list[str] = field(default_factory=list)

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
        authority_class = raw.get("authority_class")
        if authority_class is not None:
            authority_class = _bounded_text(authority_class, "authority_class", 32).strip()
            if authority_class not in AUTHORITY_CLASSES:
                raise ValueError("authority_class is invalid")
        required_evidence = _string_list(
            raw.get("required_evidence"),
            "required_evidence",
            max_items=MAX_REQUIRED_EVIDENCE,
            item_limit=128,
            pattern=PORTABLE_CAPABILITY,
        )
        data_classes = _string_list(
            raw.get("data_classes"),
            "data_classes",
            max_items=MAX_DATA_CLASSES,
            item_limit=32,
        )
        if any(value not in DATA_CLASSES for value in data_classes):
            raise ValueError("data_classes contains an invalid value")
        cost_policy_raw = raw.get("cost_policy")
        cost_policy = None
        if cost_policy_raw is not None:
            if not isinstance(cost_policy_raw, dict):
                raise ValueError("cost_policy must be an object")
            if set(cost_policy_raw) != {"cost_class", "cost_ceiling"}:
                raise ValueError("cost_policy must contain cost_class and cost_ceiling only")
            cost_class = str(cost_policy_raw["cost_class"]).strip()
            cost_ceiling = cost_policy_raw["cost_ceiling"]
            if cost_class not in COST_CLASSES:
                raise ValueError("cost_policy cost_class is invalid")
            if cost_ceiling is not None and (
                isinstance(cost_ceiling, bool)
                or not isinstance(cost_ceiling, (int, float))
                or cost_ceiling < 0
            ):
                raise ValueError("cost_policy cost_ceiling is invalid")
            cost_policy = {"cost_class": cost_class, "cost_ceiling": cost_ceiling}
        domain_dependencies = _string_list(
            raw.get("domain_dependencies"),
            "domain_dependencies",
            max_items=MAX_DOMAIN_DEPENDENCIES,
            item_limit=128,
            pattern=PORTABLE_DOMAIN_DEPENDENCY,
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
            authority_class=authority_class,
            required_evidence=required_evidence,
            data_classes=data_classes,
            cost_policy=cost_policy,
            domain_dependencies=domain_dependencies,
        )

[executed on device: daube-host-01.us-central1-a.c.disco-rope-507506-f7.internal (18782d8a-e52d-40f0-84d8-f4bc86787e89)]