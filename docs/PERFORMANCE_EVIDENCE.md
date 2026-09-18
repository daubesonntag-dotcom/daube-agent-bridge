# Performance and evidence discipline

BRIDGE² treats performance numbers as evidence only when they can be reproduced on a named environment.

## Benchmark command

Run:

```bash
python scripts/benchmark_compiler.py \
  --spec examples/skill.yaml \
  --iterations 1000 \
  --warmup 100 \
  --json-out build/evidence/benchmark.json \
  --markdown-out build/evidence/benchmark.md
```

The benchmark measures two paths:

1. **Core compile** — an already parsed `SkillSpec` compiled into provider artifacts.
2. **Load + compile** — YAML parsing plus compilation from the source spec.

Each run records:

- p50, p95 and p99 latency;
- mean/min/max latency;
- compiles per second;
- artifact count;
- output bytes;
- deterministic aggregate SHA256;
- Python implementation/version;
- operating-system/platform information;
- machine architecture;
- warm-up and measured iteration counts.

The benchmark fails if any measured compile produces a different aggregate artifact digest from the baseline compile.

## What these metrics mean

| Metric | Purpose |
|---|---|
| p50 latency | Typical compile latency |
| p95 latency | Tail latency under the measured local workload |
| p99 latency | Long-tail latency and jitter |
| compiles/s | Single-process compiler throughput |
| artifact bytes | Output volume per compile |
| artifact SHA256 | Determinism check across the generated artifact set |

These are technical performance measurements, not business outcomes. Do not translate them into hours saved, revenue impact, cost reduction, uptime, user adoption, or client results without independent evidence for those claims.

## Comparison rules

A benchmark comparison is valid only when the report preserves the environment and input information required to interpret it. Prefer the same:

- hardware/VM class;
- operating system;
- Python implementation and major/minor version;
- BRIDGE² revision;
- input spec;
- endpoint string;
- warm-up and iteration counts.

When any of these change, retain both receipts instead of overwriting the older one.

## Regression policy

Performance work should not trade away correctness, portability, readability, or security.

A proposed optimization must satisfy all release gates before it can be treated as an improvement:

1. existing tests pass;
2. Ruff passes;
3. all target families remain available;
4. generated artifact count is expected;
5. deterministic output remains deterministic;
6. provider-compatibility fixtures remain valid;
7. no new authority or secret handling is introduced;
8. benchmark methodology is unchanged or the change is explicitly documented.

For a stable benchmark environment, investigate any repeated regression in p95 latency or throughput before release. Do not set a numeric regression threshold until enough historical benchmark receipts exist to establish normal variance.

## Service-level objectives

BRIDGE² currently behaves primarily as a compiler/library plus optional MCP server. Before publishing service SLOs for a hosted endpoint, collect production telemetry first.

When a hosted service exists, define SLIs for at least:

- successful requests / total requests;
- p95 request latency;
- queue or concurrency saturation when applicable;
- MCP tool-call success rate;
- error-class distribution;
- dependency failures;
- recovery time after an incident.

Document the observation window, exclusions, measurement point and error-budget policy. A 100% reliability target is not recommended because it removes the trade-off mechanism that makes error budgets useful.

## Evidence packet for an external portfolio

A strong technical evidence packet should contain:

- public repository URL;
- immutable release/tag;
- release commit SHA;
- release asset hashes;
- `docs/VERIFICATION.md`;
- Official MCP Registry record;
- provider compatibility matrix;
- security policy and threat model;
- benchmark JSON receipt;
- benchmark Markdown receipt;
- a short demo or reproducible quick start;
- any externally confirmed outcome clearly separated from builder-reported technical metrics.

Never label builder-reported technical benchmark data as a client-confirmed business outcome.
