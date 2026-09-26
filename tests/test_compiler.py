[Reading 93 lines from start (total: 93 lines, 0 remaining)]

import json
from pathlib import Path

from daube_bridge.compiler import compile_spec, load_spec, slugify
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

def governed_sample() -> SkillSpec:
    return SkillSpec.from_dict(
        {
            "name": "Governed Audit",
            "version": "1.0.0",
            "description": "Evidence-backed audit capability.",
            "authority_class": "AUTO_A",
            "required_evidence": ["browser.receipt"],
            "data_classes": ["public", "internal"],
            "cost_policy": {"cost_class": "free", "cost_ceiling": 0},
            "domain_dependencies": ["food-safety-fnb@1.0.0"],
            "tools": [
                {
                    "name": "audit_surface",
                    "description": "Audit one surface.",
                    "parameters": {"type": "object", "properties": {}},
                }
            ],
        }
    )


def test_governance_metadata_stays_in_daube_manifest_and_skill_docs():
    artifacts = compile_spec(governed_sample())
    manifest = json.loads(artifacts["bridge/manifest.json"])
    assert manifest["authority_class"] == "AUTO_A"
    assert manifest["required_evidence"] == ["browser.receipt"]
    assert manifest["data_classes"] == ["public", "internal"]
    assert manifest["cost_policy"] == {"cost_class": "free", "cost_ceiling": 0}
    assert manifest["domain_dependencies"] == ["food-safety-fnb@1.0.0"]
    skill = artifacts["openai/SKILL.md"]
    assert "Authority class: `AUTO_A`" in skill
    assert "browser.receipt" in skill


def test_governance_metadata_does_not_leak_into_vendor_function_schemas():
    artifacts = compile_spec(governed_sample())
    for name in ["openai/functions.json", "deepseek/tools.json", "meta/tools.json", "mcp/tools.json"]:
        payload = artifacts[name]
        assert "authority_class" not in payload
        assert "required_evidence" not in payload
        assert "cost_policy" not in payload

def test_capability_fabric_example_compiles():
    spec = load_spec(Path("examples/capability-fabric-skill.yaml"))
    artifacts = compile_spec(spec)
    manifest = json.loads(artifacts["bridge/manifest.json"])
    assert manifest["authority_class"] == "AUTO_A"
    assert manifest["required_evidence"] == ["audit.observation"]
    assert manifest["cost_policy"] == {"cost_class": "free", "cost_ceiling": 0}

[executed on device: daube-host-01.us-central1-a.c.disco-rope-507506-f7.internal (18782d8a-e52d-40f0-84d8-f4bc86787e89)]