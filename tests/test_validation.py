[Reading 135 lines from start (total: 135 lines, 0 remaining)]

import pytest

from daube_bridge.model import SkillSpec


def test_rejects_missing_required_keys():
    with pytest.raises(ValueError, match="Missing required keys"):
        SkillSpec.from_dict({"name": "Broken"})


def test_rejects_empty_tools():
    with pytest.raises(ValueError, match="non-empty"):
        SkillSpec.from_dict(
            {
                "name": "Broken",
                "description": "No tools",
                "version": "0.1.0",
                "tools": [],
            }
        )


def test_default_parameter_schema():
    spec = SkillSpec.from_dict(
        {
            "name": "Small",
            "description": "Default schema test",
            "version": "0.1.0",
            "tools": [{"name": "ping", "description": "Ping"}],
        }
    )
    assert spec.tools[0]["parameters"]["type"] == "object"


def valid_tool(name: str = "ping") -> dict:
    return {
        "name": name,
        "description": "Portable test tool",
        "parameters": {"type": "object", "properties": {}},
    }


def valid_spec(**overrides) -> dict:
    data = {
        "name": "Bounded Skill",
        "description": "Validation boundary test",
        "version": "0.1.0",
        "tools": [valid_tool()],
    }
    data.update(overrides)
    return data


def test_rejects_duplicate_tool_names():
    with pytest.raises(ValueError, match="Duplicate tool name"):
        SkillSpec.from_dict(
            valid_spec(tools=[valid_tool("same_name"), valid_tool("same_name")])
        )


def test_rejects_non_portable_tool_names():
    with pytest.raises(ValueError, match="must match"):
        SkillSpec.from_dict(valid_spec(tools=[valid_tool("not portable!")] ))


def test_rejects_excessive_tool_count():
    with pytest.raises(ValueError, match="maximum of 64"):
        SkillSpec.from_dict(
            valid_spec(tools=[valid_tool(f"tool_{index}") for index in range(65)])
        )


def test_rejects_deep_parameter_schema():
    nested: dict = {"type": "string"}
    for _ in range(20):
        nested = {"type": "object", "properties": {"nested": nested}}

    with pytest.raises(ValueError, match="exceeds depth"):
        SkillSpec.from_dict(
            valid_spec(
                tools=[
                    {
                        "name": "deep",
                        "description": "Deep schema",
                        "parameters": nested,
                    }
                ]
            )
        )


def test_rejects_oversized_spec_before_compilation():
    with pytest.raises(ValueError, match="exceeds 262144 bytes"):
        SkillSpec.from_dict(valid_spec(padding="x" * 300_000))


def test_validation_does_not_mutate_caller_input():
    raw = valid_spec(tools=[{"name": "ping", "description": "Ping"}])
    SkillSpec.from_dict(raw)
    assert "parameters" not in raw["tools"][0]


def test_capability_fabric_metadata_defaults_preserve_legacy_specs():
    spec = SkillSpec.from_dict(valid_spec())
    assert spec.authority_class is None
    assert spec.required_evidence == []
    assert spec.data_classes == []
    assert spec.cost_policy is None
    assert spec.domain_dependencies == []


def test_capability_fabric_metadata_round_trips():
    spec = SkillSpec.from_dict(
        valid_spec(
            authority_class="AUTO_A",
            required_evidence=["browser.receipt", "source.ref"],
            data_classes=["public", "internal"],
            cost_policy={"cost_class": "free", "cost_ceiling": 0},
            domain_dependencies=["food-safety-fnb@1.0.0"],
        )
    )
    assert spec.authority_class == "AUTO_A"
    assert spec.required_evidence == ["browser.receipt", "source.ref"]
    assert spec.data_classes == ["public", "internal"]
    assert spec.cost_policy == {"cost_class": "free", "cost_ceiling": 0}
    assert spec.domain_dependencies == ["food-safety-fnb@1.0.0"]


def test_capability_fabric_metadata_rejects_invalid_governance_values():
    with pytest.raises(ValueError, match="authority_class"):
        SkillSpec.from_dict(valid_spec(authority_class="AUTO_Z"))
    with pytest.raises(ValueError, match="data_classes"):
        SkillSpec.from_dict(valid_spec(data_classes=["mystery"]))
    with pytest.raises(ValueError, match="cost_policy"):
        SkillSpec.from_dict(valid_spec(cost_policy={"cost_class": "mystery", "cost_ceiling": 0}))

[executed on device: daube-host-01.us-central1-a.c.disco-rope-507506-f7.internal (18782d8a-e52d-40f0-84d8-f4bc86787e89)]