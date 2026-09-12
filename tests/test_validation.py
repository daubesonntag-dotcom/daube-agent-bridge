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
