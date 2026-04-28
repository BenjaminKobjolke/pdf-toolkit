"""Unit tests for app.cli.install_global."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.cli.install_global import (
    BAT_FILES,
    InstallError,
    install_bats,
    render_bat,
)


def test_render_bat_contains_project_root_and_module() -> None:
    project_root = Path("D:/some/project")

    text = render_bat(project_root, "app.cli.swap")

    assert str(project_root) in text
    assert "app.cli.swap" in text
    assert "%*" in text  # arg forwarding
    assert "PYTHONPATH" in text
    assert ".venv\\Scripts\\python.exe" in text


def test_render_bat_uses_windows_path_separators() -> None:
    project_root = Path("D:/some/project")

    text = render_bat(project_root, "app.cli.delete_page")

    # PROJECT_ROOT should use backslashes for Windows
    assert "D:\\some\\project" in text


def test_install_bats_writes_both_files(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    target = tmp_path / "cmdtools"
    target.mkdir()

    written = install_bats(project_root, target, overwrite=False)

    assert {p.name for p in written} == {name for name, _ in BAT_FILES}
    for name, _ in BAT_FILES:
        assert (target / name).is_file()


def test_install_bats_refuses_to_overwrite_by_default(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    target = tmp_path / "cmdtools"
    target.mkdir()
    existing = target / BAT_FILES[0][0]
    existing.write_text("DO NOT OVERWRITE", encoding="utf-8")

    with pytest.raises(InstallError, match="already exist"):
        install_bats(project_root, target, overwrite=False)

    assert existing.read_text(encoding="utf-8") == "DO NOT OVERWRITE"


def test_install_bats_overwrites_when_requested(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    target = tmp_path / "cmdtools"
    target.mkdir()
    existing = target / BAT_FILES[0][0]
    existing.write_text("OLD", encoding="utf-8")

    install_bats(project_root, target, overwrite=True)

    assert existing.read_text(encoding="utf-8") != "OLD"
    assert "PYTHONPATH" in existing.read_text(encoding="utf-8")


def test_install_bats_rejects_missing_target(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    target = tmp_path / "does_not_exist"

    with pytest.raises(InstallError, match="does not exist"):
        install_bats(project_root, target, overwrite=True)


def test_install_bats_rejects_target_that_is_a_file(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    target = tmp_path / "not_a_dir"
    target.write_text("file", encoding="utf-8")

    with pytest.raises(InstallError, match="not a directory"):
        install_bats(project_root, target, overwrite=True)
