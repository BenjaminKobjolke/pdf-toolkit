"""Integration tests: flattening rectangles (and z-ordering) onto a PDF via fitz."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import fitz

from app.pdf.rect_spec import RectFieldSpec
from app.pdf.text_overlay import apply_overlay
from app.pdf.text_spec import TextFieldSpec
from tests.conftest import MakePdf


def _pixel(pdf: Path, x: int, y: int, page_index: int = 0) -> tuple[int, int, int]:
    """Return the RGB of one rendered pixel (scene px == PDF pt at zoom 1 baseline)."""
    doc = fitz.open(pdf)
    try:
        pix = doc.load_page(page_index).get_pixmap()
        return cast(tuple[int, int, int], pix.pixel(x, y))
    finally:
        doc.close()


def test_flatten_draws_filled_rect(tmp_path: Path, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400)])
    rect = RectFieldSpec(0, 40.0, 40.0, 80.0, 60.0, "#ff0000")
    out = tmp_path / "out.pdf"
    apply_overlay(pdf, (), (), (rect,), base_dir=tmp_path, output=out)
    # A point well inside the rect should be (close to) red.
    r, g, b = _pixel(out, 60, 60)
    assert r > 200 and g < 80 and b < 80


def test_z_order_later_element_wins(tmp_path: Path, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400)])
    # Two overlapping rects; the green one has the higher z, so it must be on top
    # even though it is listed first (export sorts by z, not by argument order).
    red = RectFieldSpec(0, 40.0, 40.0, 80.0, 60.0, "#ff0000", z=0.0)
    green = RectFieldSpec(0, 40.0, 40.0, 80.0, 60.0, "#00ff00", z=5.0)
    out = tmp_path / "out.pdf"
    apply_overlay(pdf, (), (), (green, red), base_dir=tmp_path, output=out)
    r, g, b = _pixel(out, 60, 60)
    assert g > 200 and r < 80 and b < 80


def test_rect_under_text_does_not_hide_text(tmp_path: Path, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400)])
    rect = RectFieldSpec(0, 10.0, 10.0, 120.0, 40.0, "#ffff00", z=0.0)
    field = TextFieldSpec(
        0, 12.0, 12.0, 100.0, 24.0, "Hello", "Helvetica", 18.0, "#000000", None, z=1.0
    )
    out = tmp_path / "out.pdf"
    apply_overlay(pdf, (field,), (), (rect,), base_dir=tmp_path, output=out)
    doc = fitz.open(out)
    try:
        assert "Hello" in doc.load_page(0).get_text()
    finally:
        doc.close()
