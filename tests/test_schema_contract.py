import json
import re
from pathlib import Path

import pytest

from daube_bridge.model import PORTABLE_TOOL_NAME, SkillSpec

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "skill.schema.json"


def _valid_spec(**overrides):
    raw = {
        "name": "Contract Skill",
        "version": "0.1.0",
        "description": "Compiler contract fixture",
        "tools": [
            {
                "name": "1portable_tool",
                "description": "Exercise the shared tool-name contract.",
                "parameters": {"type": "object", "properties": {}},
            }
        ],
        "instructions": ["Keep outputs auditable."],
        "required_capabilities": ["mcp.read"],
    }
    raw.update(overrides)
    return raw


def _tool_definition(schema):
    ref = schema["properties"]["tools"]["items"]["$ref"]
    assert ref.startswith("#/$defs/")
    return schema["$defs"][ref.rsplit("/", 1)[-1]]


def test_committed_schema_matches_runtime_contract_surface():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    assert schema["additionalProperties"] is False
    assert {"instructions", "required_capabilities"} <= set(schema["properties"])

    tool = _tool_definition(schema)
    pattern = tool["properties"]["name"]["pattern"]
    assert pattern == PORTABLE_TOOL_NAME.pattern
    assert re.fullmatch(pattern, "1portable_tool")


def test_runtime_rejects_unknown_root_fields_declared_forbidden_by_schema():
    with pytest.raises(ValueError, match="unknown|unexpected|extra"):
        SkillSpec.from_dict(_valid_spec(unexpected_contract_field=True))
