from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from daube_bridge.compiler import compile_spec, load_spec  # noqa: E402


def percentile(samples: list[float], q: float) -> float:
    if not samples:
        raise ValueError("samples must not be empty")
    ordered = sorted(samples)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q
    low = int(pos)
    high = min(low + 1, len(ordered) - 1)
    weight = pos - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def artifact_digest(artifacts: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for path, artifact_content in sorted(artifacts.items()):
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(artifact_content.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def summarize(samples_ms: list[float]) -> dict[str, float]:
    return {
        "min": round(min(samples_ms), 6),
        "mean": round(statistics.fmean(samples_ms), 6),
        "p50": round(percentile(samples_ms, 0.50), 6),
        "p95": round(percentile(samples_ms, 0.95), 6),
        "p99": round(percentile(samples_ms, 0.99), 6),
        "max": round(max(samples_ms), 6),
    }


def benchmark(
    spec_path: Path,
    iterations: int,
    warmup: int,
    endpoint: str,
) -> dict[str, Any]:
    if iterations < 1:
        raise ValueError("iterations must be >= 1")
    if warmup < 0:
        raise ValueError("warmup must be >= 0")

    spec = load_spec(spec_path)
    baseline = compile_spec(spec, endpoint=endpoint)
    baseline_hash = artifact_digest(baseline)
    output_bytes = sum(len(value.encode("utf-8")) for value in baseline.values())

    for _ in range(warmup):
        compile_spec(spec, endpoint=endpoint)

    core_samples_ms: list[float] = []
    total_start = time.perf_counter()
    for _ in range(iterations):
        start = time.perf_counter_ns()
        artifacts = compile_spec(spec, endpoint=endpoint)
        elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
        if artifact_digest(artifacts) != baseline_hash:
            raise RuntimeError("non-deterministic compiler output detected")
        core_samples_ms.append(elapsed_ms)
    core_elapsed = time.perf_counter() - total_start

    load_compile_samples_ms: list[float] = []
    total_start = time.perf_counter()
    for _ in range(iterations):
        start = time.perf_counter_ns()
        loaded = load_spec(spec_path)
        artifacts = compile_spec(loaded, endpoint=endpoint)
        elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
        if artifact_digest(artifacts) != baseline_hash:
            raise RuntimeError("non-deterministic load+compile output detected")
        load_compile_samples_ms.append(elapsed_ms)
    load_compile_elapsed = time.perf_counter() - total_start

    return {
        "schema": "daube.bridge.benchmark.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "input": {
            "spec": str(spec_path),
            "iterations": iterations,
            "warmup": warmup,
            "endpoint": endpoint,
            "tools": len(spec.tools),
        },
        "output": {
            "artifact_count": len(baseline),
            "artifact_bytes": output_bytes,
            "sha256": baseline_hash,
        },
        "compile_core": {
            "latency_ms": summarize(core_samples_ms),
            "throughput_compiles_per_second": round(iterations / core_elapsed, 3),
        },
        "load_and_compile": {
            "latency_ms": summarize(load_compile_samples_ms),
            "throughput_compiles_per_second": round(
                iterations / load_compile_elapsed, 3
            ),
        },
    }


def markdown_report(result: dict[str, Any]) -> str:
    core = result["compile_core"]
    end_to_end = result["load_and_compile"]
    env = result["environment"]
    inp = result["input"]
    out = result["output"]
    return "\n".join(
        [
            "# D'AUBE // BRIDGE² benchmark receipt",
            "",
            f"- Captured at: \`{result['captured_at']}\`",
            f"- Python: \`{env['implementation']} {env['python']}\`",
            f"- Platform: \`{env['platform']}\`",
            f"- Machine: \`{env['machine']}\`",
            f"- Spec: \`{inp['spec']}\`",
            f"- Iterations: \`{inp['iterations']}\` (+ \`{inp['warmup']}\` warmup)",
            f"- Tools in spec: \`{inp['tools']}\`",
            f"- Artifacts per compile: \`{out['artifact_count']}\`",
            f"- Output bytes per compile: \`{out['artifact_bytes']}\`",
            f"- Deterministic artifact SHA256: \`{out['sha256']}\`",
            "",
            "## Core compile",
            "",
            f"- p50: \`{core['latency_ms']['p50']} ms\`",
            f"- p95: \`{core['latency_ms']['p95']} ms\`",
            f"- p99: \`{core['latency_ms']['p99']} ms\`",
            f"- mean: \`{core['latency_ms']['mean']} ms\`",
            f"- throughput: \`{core['throughput_compiles_per_second']} compiles/s\`",
            "",
            "## Load + compile",
            "",
            f"- p50: \`{end_to_end['latency_ms']['p50']} ms\`",
            f"- p95: \`{end_to_end['latency_ms']['p95']} ms\`",
            f"- p99: \`{end_to_end['latency_ms']['p99']} ms\`",
            f"- mean: \`{end_to_end['latency_ms']['mean']} ms\`",
            f"- throughput: \`{end_to_end['throughput_compiles_per_second']} compiles/s\`",
            "",
            "> This receipt is a technical benchmark on the named environment. "
            "It is not a client-confirmed business outcome.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark BRIDGE² compile latency, throughput and determinism."
    )
    parser.add_argument("--spec", default="examples/skill.yaml")
    parser.add_argument("--iterations", type=int, default=500)
    parser.add_argument("--warmup", type=int, default=50)
    parser.add_argument("--endpoint", default="http://localhost:8000/mcp")
    parser.add_argument("--json-out")
    parser.add_argument("--markdown-out")
    args = parser.parse_args()

    result = benchmark(
        ROOT / args.spec,
        iterations=args.iterations,
        warmup=args.warmup,
        endpoint=args.endpoint,
    )

    payload = json.dumps(result, indent=2, ensure_ascii=False)
    print(payload)

    if args.json_out:
        path = ROOT / args.json_out
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload + "\n", encoding="utf-8")
    if args.markdown_out:
        path = ROOT / args.markdown_out
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown_report(result), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
