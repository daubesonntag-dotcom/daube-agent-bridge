from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "release_smoke", ROOT / "scripts" / "smoke_release.py"
)
assert SPEC and SPEC.loader
SMOKE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SMOKE)


def test_release_wheel_url_and_command_are_isolated():
    url = SMOKE.release_wheel_url("0.1.2")
    assert url.endswith("/v0.1.2/daube_agent_bridge-0.1.2-py3-none-any.whl")
    command = SMOKE.smoke_command("0.1.2")
    assert command[:3] == ["uv", "run", "--isolated"]
    assert command[-4:] == ["python", "-m", "daube_bridge", "doctor"]
    assert url in command
