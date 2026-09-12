import yaml

from daube_bridge.cli import starter_yaml
from daube_bridge.model import SkillSpec


def test_starter_yaml_is_valid():
    raw = yaml.safe_load(starter_yaml("D'AUBE Demo"))
    spec = SkillSpec.from_dict(raw)
    assert spec.name == "D'AUBE Demo"
    assert spec.tools[0]["name"] == "d_aube_demo_run"
