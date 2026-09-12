from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class SkillSpec:
    name: str
    description: str
    version: str
    tools: list[dict[str, Any]]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> SkillSpec:
        required = ("name", "description", "version", "tools")
        missing = [key for key in required if key not in raw]
        if missing:
            raise ValueError(f"Missing required keys: {', '.join(missing)}")
        if not isinstance(raw["tools"], list) or not raw["tools"]:
            raise ValueError("tools must be a non-empty list")
        for tool in raw["tools"]:
            if not isinstance(tool, dict) or "name" not in tool or "description" not in tool:
                raise ValueError("Each tool needs name and description")
            tool.setdefault("parameters", {"type": "object", "properties": {}})
        return cls(str(raw["name"]), str(raw["description"]), str(raw["version"]), raw["tools"])

