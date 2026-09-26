from daube_bridge.compiler import compile_spec, slugify
from daube_bridge.model import SkillSpec


def sample() -> SkillSpec:
    return SkillSpec.from_dict(
        {
            "name": "Demo Skill",
            "version": "0.1.0",
            "description": "A portable agent skill.",
            "tools": [
                {
                    "name": "echo",
                    "description": "Echo input.",
                    "parameters": {
                        "type": "object",
                        "properties": {"text": {"type": "string"}},
                        "required": ["text"],
                    },
                }
            ],
        }
    )


def test_slugify_is_cross_platform_safe():
    assert slugify("D'AUBE Research Radar") == "d-aube-research-radar"


def test_compile_outputs_all_surfaces():
    artifacts = compile_spec(sample())
    assert "bridge/manifest.json" in artifacts
    assert "openai/SKILL.md" in artifacts
    assert "openai/mcp-tool.json" in artifacts
    assert "deepseek/tools.json" in artifacts
    assert "deepseek/SKILL.md" in artifacts
    assert "deepseek/.agents/skills/demo-skill/SKILL.md" in artifacts
    assert "meta/tools.json" in artifacts
    assert "gemini/SKILL.md" in artifacts
    assert "claude/.mcp.json" in artifacts
    assert len(artifacts) == 17
