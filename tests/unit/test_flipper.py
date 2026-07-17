"""Unit tests for app.pdf.flipper."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest
from pypdf import PdfReader, PdfWriter

from app.pdf.flipper import flip_page
from app.pdf.rotator import ROTATE_RIGHT, rotate_page
from tests.conftest import MakePdf, PageSizesOf


def _make_left_marked_pdf(target: Path) -> Path:
    """One 100×100 page with a filled black rect in the left half only."""
    doc = fitz.open()
    page = doc.new_page(width=100, height=100)
    page.draw_rect(fitz.Rect(5, 40, 45, 60), color=(0, 0, 0), fill=(0, 0, 0))
    doc.save(str(target))
    doc.close()
    return target


def _dark_halves(pdf: Path) -> tuple[bool, bool, bool, bool]:
    """Whether the (left, right, top, bottom) halves of page 1 contain dark pixels."""
    doc = fitz.open(str(pdf))
    pix = doc[0].get_pixmap()
    width, height = pix.width, pix.height
    left = right = top = bottom = False
    for y in range(height):
        for x in range(width):
            r, g, b = pix.pixel(x, y)
            if r < 128 and g < 128 and b < 128:
                left |= x < width // 2
                right |= x >= width // 2
                top |= y < height // 2
                bottom |= y >= height // 2
    doc.close()
    return left, right, top, bottom


def test_flip_horizontal_mirrors_left_to_right(tmp_path: Path) -> None:
    source = _make_left_marked_pdf(tmp_path / "marked.pdf")
    assert _dark_halves(source)[:2] == (True, False)

    flip_page(source, page_number=1, horizontal=True)

    assert _dark_halves(source)[:2] == (False, True)


def test_flip_vertical_mirrors_top_to_bottom(tmp_path: Path) -> None:
    source = tmp_path / "marked.pdf"
    doc = fitz.open()
    page = doc.new_page(width=100, height=100)
    page.draw_rect(fitz.Rect(40, 5, 60, 45), color=(0, 0, 0), fill=(0, 0, 0))
    doc.save(str(source))
    doc.close()
    assert _dark_halves(source)[2:] == (True, False)

    flip_page(source, page_number=1, horizontal=False)

    assert _dark_halves(source)[2:] == (False, True)


def test_flip_preserves_page_count_and_sizes(make_pdf: MakePdf, page_sizes_of: PageSizesOf) -> None:
    source = make_pdf([(100, 200), (300, 400), (500, 600)])

    flip_page(source, page_number=2, horizontal=True)

    assert page_sizes_of(source) == [(100, 200), (300, 400), (500, 600)]


def test_flip_on_rotated_page_bakes_rotation(tmp_path: Path) -> None:
    source = _make_left_marked_pdf(tmp_path / "marked.pdf")
    rotate_page(source, page_number=1, degrees=ROTATE_RIGHT)
    # After a 90° CW rotation the left-half mark displays in the top half.
    assert _dark_halves(source)[2:] == (True, False)

    flip_page(source, page_number=1, horizontal=False)

    # Vertical flip of the displayed page: mark moves to the bottom half…
    assert _dark_halves(source)[2:] == (False, True)
    # …and the stored rotation flag is baked into the content.
    assert PdfReader(str(source)).pages[0].rotation == 0


def test_flip_rejects_zero_page(make_pdf: MakePdf) -> None:
    source = make_pdf([(100, 200)])
    original_bytes = source.read_bytes()

    with pytest.raises(ValueError, match="1-based"):
        flip_page(source, page_number=0, horizontal=True)

    assert source.read_bytes() == original_bytes


def test_flip_rejects_out_of_range(make_pdf: MakePdf) -> None:
    source = make_pdf([(100, 200), (300, 400)])
    original_bytes = source.read_bytes()

    with pytest.raises(ValueError, match="out of range"):
        flip_page(source, page_number=3, horizontal=True)

    assert source.read_bytes() == original_bytes


def test_flip_rejects_encrypted_pdf(tmp_path: Path) -> None:
    source = tmp_path / "encrypted.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=200)
    writer.encrypt(user_password="secret")
    with source.open("wb") as fh:
        writer.write(fh)

    with pytest.raises(ValueError, match="encrypted"):
        flip_page(source, page_number=1, horizontal=True)
