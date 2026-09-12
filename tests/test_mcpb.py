import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "dist" / "daube-agent-bridge-0.1.3.mcpb"


def test_mcpb_bundle_is_portable_and_stdio():
    subprocess.run([sys.executable, "scripts/build_mcpb.py"], cwd=ROOT, check=True)
    with zipfile.ZipFile(BUNDLE) as archive:
        names = set(archive.namelist())
        manifest = json.loads(archive.read("manifest.json"))
        entrypoint = archive.read("src/server.py").decode()

    assert manifest["manifest_version"] == "0.4"
    assert manifest["version"] == "0.1.3"
    assert manifest["server"]["type"] == "uv"
    assert manifest["server"]["mcp_config"]["command"] == "uv"
    assert "mcp.run()" in entrypoint
    assert "src/daube_bridge/server.py" in names
    assert "pyproject.toml" in names


def test_registry_title_is_valid_unicode():
    metadata = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))
    assert metadata["title"] == "D'AUBE // BRIDGE²"
