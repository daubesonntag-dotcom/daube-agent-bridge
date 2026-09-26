from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

SUPERPOWERS_REPO = "https://github.com/obra/superpowers.git"
DEFAULT_REF = "main"
BEGIN_MARKER = "<!-- daube-superpowers:begin -->"
END_MARKER = "<!-- daube-superpowers:end -->"
MANAGED_MARKER = ".daube-superpowers-managed"

BOOTSTRAP_TEXT = """\
<!-- daube-superpowers:begin -->
## D'AUBE Superpowers workflow

For non-trivial software engineering work, use the native skill catalog before implementation.
Load `using-superpowers` first when it is available, then load each matching Superpowers skill
before acting. Preserve the workflow gates: clarify/brainstorm, approve a design when needed,
write a plan, use TDD for behavior changes, review changes, and verify before declaring success.
Do not invent unavailable tools or bypass the active permission policy. When a skill requires
a capability this harness does not expose, use the skill's documented fallback or report the gap.
<!-- daube-superpowers:end -->
"""


def _run(args: list[str], *, cwd: Path | None = None) -> str:
    completed = subprocess.run(
        args,
        cwd=cwd,
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"Command failed ({completed.returncode}): {' '.join(args)}\n{detail}")
    return completed.stdout.strip()


def checkout_superpowers(cache_dir: Path, ref: str = DEFAULT_REF) -> tuple[Path, str]:
    """Fetch exactly one upstream ref without executing upstream scripts."""
    git = shutil.which("git")
    if not git:
        raise RuntimeError("Git is required to fetch Superpowers")

    cache_dir = cache_dir.expanduser().resolve()
    cache_dir.parent.mkdir(parents=True, exist_ok=True)

    if (cache_dir / ".git").is_dir():
        _run([git, "-C", str(cache_dir), "fetch", "--depth", "1", "origin", ref])
    elif cache_dir.exists():
        raise RuntimeError(f"Cache path exists but is not a Git checkout: {cache_dir}")
    else:
        _run([git, "clone", "--filter=blob:none", "--no-checkout", SUPERPOWERS_REPO, str(cache_dir)])
        _run([git, "-C", str(cache_dir), "fetch", "--depth", "1", "origin", ref])

    _run([git, "-C", str(cache_dir), "checkout", "--detach", "FETCH_HEAD"])
    commit = _run([git, "-C", str(cache_dir), "rev-parse", "HEAD"])
    return cache_dir, commit


def _managed_destination(destination: Path) -> bool:
    return (destination / MANAGED_MARKER).is_file()


def sync_skills(source_checkout: Path, project_root: Path, commit: str) -> list[str]:
    """Copy only SKILL.md bundles; never execute upstream hooks or scripts."""
    source_skills = source_checkout / "skills"
    if not source_skills.is_dir():
        raise RuntimeError(f"Superpowers skills directory not found: {source_skills}")

    target_root = project_root / ".agents" / "skills"
    target_root.mkdir(parents=True, exist_ok=True)

    installed: list[str] = []
    for source in sorted(source_skills.iterdir(), key=lambda item: item.name):
        if not source.is_dir() or not (source / "SKILL.md").is_file():
            continue
        destination = target_root / source.name
        if destination.exists() and not _managed_destination(destination):
            raise RuntimeError(f"Refusing to overwrite unmanaged skill directory: {destination}")
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination)
        (destination / MANAGED_MARKER).write_text(
            f"source={SUPERPOWERS_REPO}\ncommit={commit}\n",
            encoding="utf-8",
        )
        installed.append(source.name)

    if not installed:
        raise RuntimeError("No Superpowers SKILL.md bundles were discovered")
    return installed


def ensure_project_bootstrap(project_root: Path) -> Path:
    """Idempotently inject a project-scoped Harness/agent bootstrap."""
    path = project_root / "AGENTS.local.md"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""

    start = existing.find(BEGIN_MARKER)
    end = existing.find(END_MARKER)
    if start >= 0 and end >= 0 and end >= start:
        end += len(END_MARKER)
        updated = existing[:start].rstrip() + "\n\n" + BOOTSTRAP_TEXT.rstrip() + existing[end:]
    elif start >= 0 or end >= 0:
        raise RuntimeError(f"Malformed D'AUBE Superpowers markers in {path}")
    else:
        prefix = existing.rstrip()
        updated = (prefix + "\n\n" if prefix else "") + BOOTSTRAP_TEXT.rstrip() + "\n"

    path.write_text(updated, encoding="utf-8")
    return path


def install_gemini_extension() -> str:
    """Use Gemini CLI's native extension mechanism when Gemini is installed."""
    gemini = shutil.which("gemini")
    if not gemini:
        return "not-installed"

    listing = subprocess.run(
        [gemini, "extensions", "list"],
        check=False,
        text=True,
        capture_output=True,
    )
    text = (listing.stdout + "\n" + listing.stderr).lower()
    if listing.returncode == 0 and "superpowers" in text:
        _run([gemini, "extensions", "update", "superpowers"])
        return "updated"

    _run([gemini, "extensions", "install", SUPERPOWERS_REPO])
    return "installed"


def write_provenance(
    source_checkout: Path,
    project_root: Path,
    *,
    ref: str,
    commit: str,
    skills: list[str],
    gemini_status: str,
) -> Path:
    provenance_dir = project_root / ".daube" / "superpowers"
    provenance_dir.mkdir(parents=True, exist_ok=True)

    source_license = source_checkout / "LICENSE"
    if source_license.is_file():
        shutil.copy2(source_license, provenance_dir / "LICENSE")

    notice = provenance_dir / "NOTICE.md"
    notice.write_text(
        "# Superpowers provenance\n\n"
        f"- Upstream: {SUPERPOWERS_REPO}\n"
        f"- Requested ref: `{ref}`\n"
        f"- Resolved commit: `{commit}`\n"
        "- Integration: project-local `.agents/skills` plus `AGENTS.local.md` bootstrap.\n"
        "- Upstream skill bodies are copied verbatim; D'AUBE does not rewrite them.\n",
        encoding="utf-8",
    )

    lock = provenance_dir / "lock.json"
    lock.write_text(
        json.dumps(
            {
                "schema": "daube.superpowers-lock.v1",
                "upstream": SUPERPOWERS_REPO,
                "ref": ref,
                "commit": commit,
                "skills": skills,
                "gemini_extension": gemini_status,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return lock


def bootstrap_superpowers(
    project_root: str | Path,
    *,
    ref: str = DEFAULT_REF,
    cache_dir: str | Path | None = None,
    install_gemini: bool = True,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Project root does not exist: {root}")

    cache = (
        Path(cache_dir).expanduser()
        if cache_dir is not None
        else Path.home() / ".cache" / "daube" / "superpowers"
    )
    checkout, commit = checkout_superpowers(cache, ref=ref)
    skills = sync_skills(checkout, root, commit)
    bootstrap = ensure_project_bootstrap(root)
    gemini_status = install_gemini_extension() if install_gemini else "skipped"
    lock = write_provenance(
        checkout,
        root,
        ref=ref,
        commit=commit,
        skills=skills,
        gemini_status=gemini_status,
    )
    return {
        "project_root": str(root),
        "ref": ref,
        "commit": commit,
        "skills": skills,
        "bootstrap": str(bootstrap),
        "lock": str(lock),
        "gemini_extension": gemini_status,
    }
