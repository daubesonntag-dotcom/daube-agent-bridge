from __future__ import annotations

import argparse
import subprocess

REPO = "daubesonntag-dotcom/daube-agent-bridge"


def release_wheel_url(version: str) -> str:
    version = version.removeprefix("v")
    filename = f"daube_agent_bridge-{version}-py3-none-any.whl"
    return f"https://github.com/{REPO}/releases/download/v{version}/{filename}"


def smoke_command(version: str) -> list[str]:
    return [
        "uv", "run", "--isolated", "--with", release_wheel_url(version),
        "python", "-m", "daube_bridge", "doctor",
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test a public BRIDGE² release wheel.")
    parser.add_argument("version", help="Release version, for example 0.1.2")
    args = parser.parse_args()
    subprocess.run(smoke_command(args.version), check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
