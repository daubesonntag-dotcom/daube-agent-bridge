# Skill artifact hardening source verification

Date: 2026-10-04. Branch: `codex/skill-artifact-hardening`.
Base revision: `56af43fb3fc55cc916dd92d060ce2ff5e9547cbf` plus this working-tree change.
Environment: Windows, Python 3.13.15, Ruff 0.16.6.

## Changes and compatibility

`src/daube_bridge/compiler.py` now serializes skill frontmatter with the existing PyYAML dependency. A valid description containing `:`, comments, newlines, `---`, boolean-like text, Vietnamese, emoji or Unicode line separators remains exactly one description string across all generated SKILL.md files. Description text cannot introduce another frontmatter key.

`tests/test_compiler.py` covers these cases by parsing generated YAML and comparing the complete mapping. Four initial cases failed before the fix. A fifth Unicode case exposed a JSON-string quoting fallback's NEL normalization; the final YAML serializer passes it.

The required Ruff gate exposed existing type-exception and benchmark formatting problems. `src/daube_bridge/model.py` now raises `TypeError` for non-string schema keys, non-list instruction/capability containers, non-object tools, non-object parameter schemas and non-object properties. Invalid values, limits and missing fields retain their existing validation behavior. Consumers catching only `ValueError` for those malformed types must also catch `TypeError`. Five regressions in `tests/test_validation.py` failed before this change and passed afterward.

`scripts/benchmark_compiler.py` retains source-local compiler import after setting the path, uses `datetime.UTC` and explicit concatenation. `mcpb/src/server.py` has import-spacing cleanup. No validation or lint rules were disabled.

## Fresh checks

- `python -m pytest -q -p no:cacheprovider`: 36 passed, with 4 existing FastMCP annotation deprecation warnings.
- `ruff check .`: all checks passed.
- `python scripts/verify.py`: passed tests, source/test lint, 7-target doctor, 15-artifact sample compilation and wheel build.
- `python scripts/build_mcpb.py`: passed. The full suite also covers deterministic bundle generation.
- Installed the locally built wheel with `--no-deps --target .git/release-wheel-smoke`; verified the imported package came from that target, generated 15 artifacts and preserved multiline frontmatter descriptions exactly.
- `git diff --check`: passed (Git emitted local LF/CRLF conversion notices).

Local candidate artifacts retain the existing version and were not published:

| Artifact | SHA-256 |
| --- | --- |
| `dist/daube_agent_bridge-0.1.3-py3-none-any.whl` | `d3b1ddfd8da3660acfe5e71b6d9cd56d03d35d3501e045e8ddf759a0e25f80ee` |
| `dist/daube-agent-bridge-0.1.3.mcpb` | `a4411b1243649dd350aac554fefac4bf99e7babce7113b0a8d4a7f1c248d04d6` |

## Unverified boundaries

These checks do not establish deployed MCP availability or downstream provider/runtime behavior. The official MCP Registry validator was unavailable at `.tools/mcp-publisher.exe` and was not run. No public release smoke, CI dispatch, version/tag change, publication or deployment occurred. The candidate hashes above are local builds, not hashes for the historical public v0.1.3 release.
