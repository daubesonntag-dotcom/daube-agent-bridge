from __future__ import annotations

import json
import subprocess
import urllib.parse
import urllib.request
from datetime import UTC, datetime

REPO = "daubesonntag-dotcom/daube-agent-bridge"
REGISTRY = "https://registry.modelcontextprotocol.io/v0.1/servers"


def summarize(repo: dict, releases: list[dict], registry: dict) -> dict:
    latest = next(
        (item for item in registry.get("servers", [])
         if item.get("_meta", {}).get("io.modelcontextprotocol.registry/official", {}).get("isLatest")),
        {},
    )
    official = latest.get("_meta", {}).get("io.modelcontextprotocol.registry/official", {})
    server = latest.get("server", {})
    return {
        "stars": repo.get("stargazers_count", 0),
        "forks": repo.get("forks_count", 0),
        "subscribers": repo.get("subscribers_count", 0),
        "open_issues": repo.get("open_issues_count", 0),
        "release_count": len(releases),
        "release_downloads": sum(
            asset.get("download_count", 0) for release in releases for asset in release.get("assets", [])
        ),
        "latest_release": releases[0].get("tag_name") if releases else None,
        "registry_version": server.get("version"),
        "registry_status": official.get("status"),
    }


def gh_json(path: str) -> object:
    raw = subprocess.check_output(["gh", "api", path], text=True, encoding="utf-8")
    return json.loads(raw)


def fetch_registry() -> dict:
    query = urllib.parse.urlencode({"search": f"io.github.{REPO}"})
    with urllib.request.urlopen(f"{REGISTRY}?{query}", timeout=15) as response:
        return json.load(response)


def main() -> int:
    repo = gh_json(f"repos/{REPO}")
    releases = gh_json(f"repos/{REPO}/releases?per_page=100")
    snapshot = summarize(repo, releases, fetch_registry())
    snapshot["captured_at"] = datetime.now(UTC).isoformat()
    snapshot["repository"] = REPO
    print(json.dumps(snapshot, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
