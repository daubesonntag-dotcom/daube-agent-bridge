from __future__ import annotations

from pathlib import Path

import pytest

from daube_bridge.superpowers import (
    BEGIN_MARKER,
    END_MARKER,
    ensure_project_bootstrap,
    sync_skills,
)


def _upstream(tmp_path: Path) -> Path:
    source = tmp_path / "upstream"
    for name in ("using-superpowers", "brainstorming"):
        skill = source / "skills" / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: test\n---\n# {name}\n",
            encoding="utf-8",
        )
    return source


def test_sync_skills_copies_bundles_and_marks_ownership(tmp_path: Path):
    source = _upstream(tmp_path)
    project = tmp_path / "project"
    project.mkdir()

    installed = sync_skills(source, project, "abc123")

    assert installed == ["brainstorming", "using-superpowers"]
    target = project / ".agents" / "skills" / "using-superpowers"
    assert (target / "SKILL.md").is_file()
    marker = (target / ".daube-superpowers-managed").read_text(encoding="utf-8")
    assert "commit=abc123" in marker


def test_sync_skills_refuses_to_overwrite_unmanaged_skill(tmp_path: Path):
    source = _upstream(tmp_path)
    project = tmp_path / "project"
    conflict = project / ".agents" / "skills" / "brainstorming"
    conflict.mkdir(parents=True)
    (conflict / "SKILL.md").write_text("custom", encoding="utf-8")

    with pytest.raises(RuntimeError, match="unmanaged"):
        sync_skills(source, project, "abc123")

    assert (conflict / "SKILL.md").read_text(encoding="utf-8") == "custom"


def test_project_bootstrap_is_idempotent_and_preserves_existing_text(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    path = project / "AGENTS.local.md"
    path.write_text("# Existing\n\nKeep me.\n", encoding="utf-8")

    ensure_project_bootstrap(project)
    ensure_project_bootstrap(project)

    content = path.read_text(encoding="utf-8")
    assert content.startswith("# Existing")
    assert "Keep me." in content
    assert content.count(BEGIN_MARKER) == 1
    assert content.count(END_MARKER) == 1
