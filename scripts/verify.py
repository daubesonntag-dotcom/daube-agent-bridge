from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def source_env() -> dict[str, str]:
    env = os.environ.copy()
    src = str(ROOT / 'src')
    current = env.get('PYTHONPATH')
    env['PYTHONPATH'] = src if not current else src + os.pathsep + current
    return env


def bridge_args(*args: str) -> tuple[str, ...]:
    return (sys.executable, '-m', 'daube_bridge', *args)


def run(*args: str, env: dict[str, str] | None = None) -> None:
    print('+', ' '.join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True, env=env)


def main() -> int:
    run(sys.executable, '-m', 'pytest', '-q')
    run('ruff', 'check', 'src', 'tests')
    env = source_env()
    run(*bridge_args('doctor'), env=env)
    run(*bridge_args('compile', 'examples/skill.yaml', '-o', 'build/verify'), env=env)
    run(sys.executable, '-m', 'pip', 'wheel', '.', '--no-deps', '-w', 'dist')
    wheels = sorted((ROOT / 'dist').glob('*.whl'), key=lambda p: p.stat().st_mtime)
    wheel = wheels[-1]
    digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    print(f'VERIFIED: {wheel.name}')
    print(f'SHA256: {digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
