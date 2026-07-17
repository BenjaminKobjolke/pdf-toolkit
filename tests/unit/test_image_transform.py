"""Unit tests for app.pdf.image_transform."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest
from PIL import Image

from app.pdf.image_transform import flip_image, rotate_image

RED = (255, 0, 0)
BLUE = (0, 0, 255)


def _make_rb_row(target: Path) -> Path:
    """A 2×1 PNG: red pixel left, blue pixel right."""
    img = Image.new("RGB", (2, 1))
    img.putpixel((0, 0), RED)
    img.putpixel((1, 0), BLUE)
    img.save(target)
    return target


def _pixels(path: Path) -> list[tuple[int, ...]]:
    with Image.open(path) as img:
        return [img.getpixel(xy) for xy in _coords(img)]


def _coords(img: Image.Image) -> list[tuple[int, int]]:
    return [(x, y) for y in range(img.height) for x in range(img.width)]


def _size(path: Path) -> tuple[int, int]:
    with Image.open(path) as img:
        return cast(tuple[int, int], img.size)


def test_rotate_90_clockwise_turns_row_into_column(tmp_path: Path) -> None:
    source = _make_rb_row(tmp_path / "row.png")

    rotate_image(source, 90)

    assert _size(source) == (1, 2)
    assert _pixels(source) == [RED, BLUE]  # red on top


def test_rotate_270_clockwise_puts_left_pixel_at_bottom(tmp_path: Path) -> None:
    source = _make_rb_row(tmp_path / "row.png")

    rotate_image(source, 270)

    assert _size(source) == (1, 2)
    assert _pixels(source) == [BLUE, RED]  # blue on top


def test_rotate_180_reverses_row(tmp_path: Path) -> None:
    source = _make_rb_row(tmp_path / "row.png")

    rotate_image(source, 180)

    assert _size(source) == (2, 1)
    assert _pixels(source) == [BLUE, RED]


def test_rotate_rejects_non_multiple_of_90(tmp_path: Path) -> None:
    source = _make_rb_row(tmp_path / "row.png")
    original_bytes = source.read_bytes()

    with pytest.raises(ValueError, match="multiple of 90"):
        rotate_image(source, 45)

    assert source.read_bytes() == original_bytes


def test_flip_horizontal_swaps_left_and_right(tmp_path: Path) -> None:
    source = _make_rb_row(tmp_path / "row.png")

    flip_image(source, horizontal=True)

    assert _size(source) == (2, 1)
    assert _pixels(source) == [BLUE, RED]


def test_flip_vertical_swaps_top_and_bottom(tmp_path: Path) -> None:
    source = tmp_path / "col.png"
    img = Image.new("RGB", (1, 2))
    img.putpixel((0, 0), RED)
    img.putpixel((0, 1), BLUE)
    img.save(source)

    flip_image(source, horizontal=False)

    assert _pixels(source) == [BLUE, RED]


def test_flip_vertical_keeps_row_unchanged_in_content(tmp_path: Path) -> None:
    source = _make_rb_row(tmp_path / "row.png")

    flip_image(source, horizontal=False)

    assert _pixels(source) == [RED, BLUE]


def test_png_stays_png(tmp_path: Path) -> None:
    source = _make_rb_row(tmp_path / "row.png")

    rotate_image(source, 90)

    with Image.open(source) as img:
        assert img.format == "PNG"


def test_jpeg_stays_jpeg(tmp_path: Path) -> None:
    source = tmp_path / "photo.jpg"
    Image.new("RGB", (4, 2), RED).save(source)

    rotate_image(source, 90)

    assert _size(source) == (2, 4)
    with Image.open(source) as img:
        assert img.format == "JPEG"


def test_rgba_mode_survives(tmp_path: Path) -> None:
    source = tmp_path / "alpha.png"
    Image.new("RGBA", (2, 1), (10, 200, 50, 128)).save(source)

    flip_image(source, horizontal=True)

    with Image.open(source) as img:
        assert img.mode == "RGBA"


def test_no_tmp_file_left_behind(tmp_path: Path) -> None:
    source = _make_rb_row(tmp_path / "row.png")

    rotate_image(source, 90)
    flip_image(source, horizontal=True)

    assert list(tmp_path.glob("*.tmp")) == []
