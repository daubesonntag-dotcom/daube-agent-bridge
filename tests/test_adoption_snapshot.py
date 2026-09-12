from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "adoption_snapshot", ROOT / "scripts" / "adoption_snapshot.py"
)
assert SPEC and SPEC.loader
SNAPSHOT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SNAPSHOT)


def test_summarize_reports_real_counts_and_latest_registry_version():
    repo = {"stargazers_count": 3, "forks_count": 2, "subscribers_count": 1}
    releases = [{"assets": [{"download_count": 4}, {"download_count": 6}]}]
    registry = {"servers": [{"server": {"version": "0.1.2"}, "_meta": {
        "io.modelcontextprotocol.registry/official": {"status": "active", "isLatest": True}
    }}]}
    result = SNAPSHOT.summarize(repo, releases, registry)
    assert result["stars"] == 3
    assert result["release_downloads"] == 10
    assert result["registry_version"] == "0.1.2"
    assert result["registry_status"] == "active"
