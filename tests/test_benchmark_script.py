from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "benchmark_compiler.py"


def load_benchmark_module():
    spec = importlib.util.spec_from_file_location("bridge_benchmark", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_percentile_interpolates():
    module = load_benchmark_module()
    assert module.percentile([1.0, 2.0, 3.0], 0.5) == 2.0


def test_benchmark_smoke():
    module = load_benchmark_module()
    result = module.benchmark(
        ROOT / "examples" / "skill.yaml",
        iterations=3,
        warmup=1,
        endpoint="http://localhost:8000/mcp",
    )

    assert result["schema"] == "daube.bridge.benchmark.v1"
    assert result["output"]["artifact_count"] == 15
    assert len(result["output"]["sha256"]) == 64
    assert result["compile_core"]["latency_ms"]["p95"] >= 0
    assert result["compile_core"]["throughput_compiles_per_second"] > 0
    assert result["load_and_compile"]["throughput_compiles_per_second"] > 0
