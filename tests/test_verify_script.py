from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("bridge_verify", ROOT / "scripts" / "verify.py")
assert SPEC and SPEC.loader
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


def test_verify_bridge_command_targets_current_source():
    assert VERIFY.bridge_args("doctor") == (
        sys.executable,
        "-m",
        "daube_bridge",
        "doctor",
    )
    first_path = VERIFY.source_env()["PYTHONPATH"].split(os.pathsep)[0]
    assert Path(first_path).resolve() == (ROOT / "src").resolve()
