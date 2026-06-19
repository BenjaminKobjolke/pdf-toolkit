"""Unit tests for the release identity (version + build)."""

from __future__ import annotations

from importlib import metadata
from pathlib import Path

import pytest

from app.release import release_info
from app.release.release_info import ReleaseId


def test_label_combines_version_and_build() -> None:
    assert ReleaseId("0.1.0", 22).label == "0.1.0_22"


def test_current_version_uses_package_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(metadata, "version", lambda name: "1.2.3")
    assert release_info.current_version() == "1.2.3"


def test_current_version_falls_back_to_pyproject(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(name: str) -> str:
        raise metadata.PackageNotFoundError(name)

    monkeypatch.setattr(metadata, "version", _raise)
    # The repo's pyproject.toml is the fallback source in a source checkout.
    assert release_info.current_version() != ""


def test_current_build_reads_bundled_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "build_version.txt").write_text("42", encoding="utf-8")
    import app.gui.resources as resources

    monkeypatch.setattr(resources, "bundled_root", lambda: tmp_path)
    assert release_info.current_build() == 42


def test_current_release_bundles_both(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(release_info, "current_version", lambda: "0.1.0")
    monkeypatch.setattr(release_info, "current_build", lambda: 5)
    assert release_info.current_release() == ReleaseId("0.1.0", 5)
