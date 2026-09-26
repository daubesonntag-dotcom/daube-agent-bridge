from __future__ import annotations

import argparse
import platform
import sys
from pathlib import Path

from .compiler import TARGETS, compile_spec, load_spec, slugify, write_artifacts
from .superpowers import bootstrap_superpowers


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="daube-bridge",
        description="Compile one AI skill spec into multi-agent artifacts.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Create a starter skill YAML")
    init.add_argument("path", nargs="?", default="skill.yaml")
    init.add_argument("--name", default="My Portable Skill")

    validate = sub.add_parser("validate", help="Validate a skill YAML spec")
    validate.add_argument("spec")

    compile_cmd = sub.add_parser("compile", help="Compile a skill YAML spec")
    compile_cmd.add_argument("spec")
    compile_cmd.add_argument("-o", "--out", default="dist")
    compile_cmd.add_argument("--endpoint", default="http://localhost:8000/mcp")

    doctor = sub.add_parser("doctor", help="Check local BRIDGE² readiness")
    doctor.add_argument("--endpoint", default="http://localhost:8000/mcp")

    superpowers = sub.add_parser(
        "superpowers",
        help="Sync the upstream Superpowers workflow into a project",
    )
    superpowers.add_argument("--project", default=".")
    superpowers.add_argument("--ref", default="main")
    superpowers.add_argument("--cache-dir")
    superpowers.add_argument(
        "--skip-gemini",
        action="store_true",
        help="Do not install/update the official Gemini CLI extension",
    )

    serve = sub.add_parser("serve", help="Run the D'AUBE MCP server")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    return parser


def starter_yaml(name: str) -> str:
    slug = slugify(name).replace("-", "_")
    return (
        f"name: {name}\n"
        "version: 0.1.0\n"
        "description: A portable AI capability compiled by D'AUBE BRIDGE².\n"
        "tools:\n"
        f"  - name: {slug}_run\n"
        "    description: Run the portable capability.\n"
        "    parameters:\n"
        "      type: object\n"
        "      properties:\n"
        "        input:\n"
        "          type: string\n"
        "      required: [input]\n"
    )


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "init":
        path = Path(args.path)
        if path.exists():
            print(f"Refusing to overwrite existing file: {path}", file=sys.stderr)
            return 2
        path.write_text(starter_yaml(args.name), encoding="utf-8")
        print(f"Created {path}")
        return 0

    if args.command == "doctor":
        print(f"Python: {platform.python_version()}")
        print(f"Targets ({len(TARGETS)}): {', '.join(TARGETS)}")
        print(f"Default endpoint: {args.endpoint}")
        print("Status: ready")
        return 0

    if args.command == "superpowers":
        result = bootstrap_superpowers(
            args.project,
            ref=args.ref,
            cache_dir=args.cache_dir,
            install_gemini=not args.skip_gemini,
        )
        print(f"Superpowers commit: {result['commit']}")
        print(f"Project: {result['project_root']}")
        print(f"Skills installed: {len(result['skills'])}")
        print(f"Gemini extension: {result['gemini_extension']}")
        print(f"Provenance lock: {result['lock']}")
        return 0

    if args.command == "serve":
        from .server import mcp

        mcp.run(transport="http", host=args.host, port=args.port)
        return 0

    spec = load_spec(args.spec)
    if args.command == "validate":
        print(f"OK: {spec.name} {spec.version}")
        print("Targets:", ", ".join(TARGETS))
        return 0

    artifacts = compile_spec(spec, endpoint=args.endpoint)
    written = write_artifacts(artifacts, args.out)
    print(f"Compiled {spec.name} -> {len(written)} artifacts")
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
