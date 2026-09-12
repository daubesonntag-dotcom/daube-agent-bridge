from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args: str) -> None:
    print('+', ' '.join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> int:
    run(sys.executable, '-m', 'pytest', '-q')
    run('ruff', 'check', 'src', 'tests')
    run('daube-bridge', 'doctor')
    run('daube-bridge', 'compile', 'examples/skill.yaml', '-o', 'build/verify')
    run(sys.executable, '-m', 'pip', 'wheel', '.', '--no-deps', '-w', 'dist')
    wheels = sorted((ROOT / 'dist').glob('*.whl'), key=lambda p: p.stat().st_mtime)
    wheel = wheels[-1]
    digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    print(f'VERIFIED: {wheel.name}')
    print(f'SHA256: {digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
