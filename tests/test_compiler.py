import pytest
import yaml

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
    assert "meta/tools.json" in artifacts
    assert "gemini/SKILL.md" in artifacts
    assert "claude/.mcp.json" in artifacts
    assert len(artifacts) == 15


@pytest.mark.parametrize("description", [
    "Research: compare options",
    "First line\nallowed-tools: shell\n---\nSecond line",
    "# A description with YAML punctuation: [yes, no]",
    "true",
    "Tiếng Việt 🎨\u0085next\u2028line\u2029paragraph",
])
def test_skill_frontmatter_preserves_description_as_one_string(description):
    spec = sample()
    spec.description = description
    for path, content in compile_spec(spec).items():
        if path.endswith("SKILL.md"):
            frontmatter = content.split("\n---\n", 1)[0].removeprefix("---\n")
            assert yaml.safe_load(frontmatter) == {
                "name": "demo-skill", "description": description,
            }, path
