# BRIDGE² 20K Star Operating Target

20,000 GitHub stars is an adoption target, not a guaranteed external outcome. The project will optimize for real usage, repeatable distribution, and ecosystem relevance; fake, purchased, or automated stars are out of scope.

## Pace math

- 90-day stretch: 222 net stars/day.
- 180-day operating target: 111 net stars/day.
- 365-day floor: 55 net stars/day.

## Benchmark snapshot — 2026-09-12

| Repository | Stars | Lifetime average |
|---|---:|---:|
| anthropics/skills | 175,868 | ~496/day |
| browser-use/browser-use | 114,269 | ~168/day |
| modelcontextprotocol/servers | 90,258 | ~136/day |
| upstash/context7 | 61,900 | ~116/day |
| microsoft/playwright-mcp | 37,025 | ~69/day |
| czlonkowski/n8n-mcp | 22,875 | ~50/day |
| PrefectHQ/fastmcp | 27,624 | ~42/day |

The 180-day target requires Context7-class sustained velocity. The 90-day target requires launch velocity above browser-use's lifetime average.

## Growth loops

1. **Utility loop:** one spec → many providers → fewer integration rewrites.
2. **Compatibility loop:** every provider change becomes a fixture, issue, patch, and searchable release note.
3. **Contributor loop:** adapter requests are intentionally small, documented, and suitable for first-time contributors.
4. **Distribution loop:** ship to MCP directories, provider communities, package indexes, developer forums, launch sites, and relevant subreddits without spam.
5. **Content loop:** turn every compatibility benchmark and release into a short demo, tutorial, and changelog artifact.

## Milestone gates

- 0→100: launch quality, install friction, README clarity, first external users.
- 100→1K: directory listings, integrations, external PRs, tutorial content.
- 1K→5K: framework adapters, package distribution, benchmarks, maintainer partnerships.
- 5K→20K: ecosystem standardization, registry/search, major provider integrations, conference/community visibility.

## Metrics

Track stars/day, clones, unique visitors, forks, contributors, issues opened by non-maintainers, package downloads, MCP installs, docs referrals, release adoption, and star-to-install conversion. Optimize for installs and retained contributors first; stars should follow utility.

For a reproducible public snapshot of repository, release-asset, and Official MCP Registry metrics, run:

```bash
python scripts/adoption_snapshot.py
```
