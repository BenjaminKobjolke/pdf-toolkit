"""Unit tests for image asset copying and path resolution."""

from __future__ import annotations

from pathlib import Path

from app.pdf.image_assets import assets_dir, copy_into_assets, resolve_image_path
from tests.conftest import MakeImage


def test_copy_into_assets_creates_relative_copy(tmp_path: Path, make_image: MakeImage) -> None:
    img = make_image("png", name="sig.png")
    base = tmp_path / "doc"
    base.mkdir()
    rel = copy_into_assets(img, base)
    assert rel == "assets/sig.png"
    assert (base / "assets" / "sig.png").is_file()


def test_copy_into_assets_dedups_names(tmp_path: Path, make_image: MakeImage) -> None:
    img = make_image("png", name="sig.png")
    base = tmp_path / "doc"
    base.mkdir()
    assert copy_into_assets(img, base) == "assets/sig.png"
    assert copy_into_assets(img, base) == "assets/sig_1.png"
    assert (base / "assets" / "sig_1.png").is_file()


def test_resolve_relative_against_base(tmp_path: Path) -> None:
    assert resolve_image_path("assets/x.png", False, tmp_path) == tmp_path / "assets" / "x.png"


def test_resolve_absolute_returned_as_is(tmp_path: Path) -> None:
    abs_path = tmp_path / "elsewhere" / "y.png"
    assert resolve_image_path(str(abs_path), True, tmp_path) == abs_path


def test_assets_dir(tmp_path: Path) -> None:
    assert assets_dir(tmp_path) == tmp_path / "assets"
