from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.3"
OUT = ROOT / "dist" / f"daube-agent-bridge-{VERSION}.mcpb"
FIXED_TIME = (2020, 1, 1, 0, 0, 0)

files = {
    "manifest.json": ROOT / "mcpb" / "manifest.json",
    "pyproject.toml": ROOT / "mcpb" / "pyproject.toml",
    "src/server.py": ROOT / "mcpb" / "src" / "server.py",
}
for source in sorted((ROOT / "src" / "daube_bridge").glob("*.py")):
    files[f"src/daube_bridge/{source.name}"] = source

OUT.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for name in sorted(files):
        info = zipfile.ZipInfo(name, FIXED_TIME)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        archive.writestr(info, files[name].read_bytes())

digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
print(f"MCPB={OUT}")
print(f"SHA256={digest}")
