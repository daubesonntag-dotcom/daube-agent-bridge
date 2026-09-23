import json
from pathlib import Path

from daube_bridge.compiler import compile_spec, load_spec

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = (
    ROOT / "examples" / "pro-parity" / "research.yaml",
    ROOT / "examples" / "pro-parity" / "coding.yaml",
    ROOT / "examples" / "pro-parity" / "browser.yaml",
    ROOT / "examples" / "pro-parity" / "runtime-recovery.yaml",
)


def test_pro_parity_fixtures_compile_deterministically_across_targets():
    for path in FIXTURES:
        spec = load_spec(path)
        first = compile_spec(spec)
        second = compile_spec(spec)
        assert first == second
        assert len(first) == 15

        manifest = json.loads(first["bridge/manifest.json"])
        assert manifest["instructions"] == spec.instructions
        assert manifest["required_capabilities"] == spec.required_capabilities

        instruction_marker = "## Operating instructions"
        capability_marker = "## Required capabilities"
        assert instruction_marker in first["openai/SKILL.md"]
        assert instruction_marker in first["claude/skills/" + manifest["slug"] + "/SKILL.md"]
        assert instruction_marker in first["gemini/SKILL.md"]
        assert capability_marker in first["openai/SKILL.md"]

        assert "deepseek/tools.json" in first
        assert "meta/tools.json" in first
        assert "mcp/tools.json" in first
        assert "browser/manifest.json" in first


def test_legacy_skill_contract_remains_backward_compatible():
    spec = load_spec(ROOT / "examples" / "skill.yaml")
    artifacts = compile_spec(spec)
    assert spec.instructions == []
    assert spec.required_capabilities == []
    assert len(artifacts) == 15
