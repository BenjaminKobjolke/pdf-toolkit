"""Unit tests for the PNG-to-ICO conversion tool."""

from __future__ import annotations

from pathlib import Path

from PIL import IcoImagePlugin, Image

from tools.png_to_ico import ICON_SIZES, convert


def _embedded_sizes(ico: Path) -> set[tuple[int, int]]:
    with ico.open("rb") as handle:
        return IcoImagePlugin.IcoImageFile(handle).ico.sizes()


def test_convert_writes_square_frames_from_non_square_source(tmp_path: Path) -> None:
    src = tmp_path / "icon.png"
    Image.new("RGBA", (604, 584), (255, 0, 0, 255)).save(src)
    dst = tmp_path / "icon.ico"

    convert(src, dst)

    assert dst.is_file()
    assert _embedded_sizes(dst) == set(ICON_SIZES)


def test_convert_keeps_square_source_square(tmp_path: Path) -> None:
    src = tmp_path / "icon.png"
    Image.new("RGBA", (512, 512), (0, 128, 255, 255)).save(src)
    dst = tmp_path / "icon.ico"

    convert(src, dst)

    assert _embedded_sizes(dst) == set(ICON_SIZES)
