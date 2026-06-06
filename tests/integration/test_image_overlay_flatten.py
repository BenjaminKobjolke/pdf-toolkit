"""Integration tests: flattening images (and text+images) onto a PDF via fitz."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from app.pdf.image_spec import ImageFieldSpec
from app.pdf.text_overlay import apply_overlay
from app.pdf.text_spec import TextFieldSpec
from tests.conftest import MakeImage, MakePdf


def _image_count(pdf: Path, page_index: int = 0) -> int:
    doc = fitz.open(pdf)
    try:
        return len(doc.load_page(page_index).get_images())
    finally:
        doc.close()


def test_flatten_draws_image(tmp_path: Path, make_pdf: MakePdf, make_image: MakeImage) -> None:
    pdf = make_pdf([(300, 400)])
    img = make_image("rgba_png", size=(40, 20))
    spec = ImageFieldSpec(0, 30.0, 30.0, 60.0, 30.0, str(img), absolute=True)
    out = tmp_path / "out.pdf"
    apply_overlay(pdf, (), (spec,), base_dir=tmp_path, output=out)
    assert _image_count(out) >= 1


def test_flatten_text_and_image_together(
    tmp_path: Path, make_pdf: MakePdf, make_image: MakeImage
) -> None:
    pdf = make_pdf([(300, 400)])
    img = make_image("png")
    field = TextFieldSpec(0, 10.0, 10.0, 80.0, 24.0, "Hello", "Helvetica", 18.0, "#000000", None)
    image = ImageFieldSpec(0, 60.0, 60.0, 30.0, 30.0, str(img), absolute=True)
    out = tmp_path / "out.pdf"
    apply_overlay(pdf, (field,), (image,), base_dir=tmp_path, output=out)
    doc = fitz.open(out)
    try:
        page = doc.load_page(0)
        assert "Hello" in page.get_text()
        assert len(page.get_images()) >= 1
    finally:
        doc.close()


def test_missing_asset_raises(tmp_path: Path, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400)])
    spec = ImageFieldSpec(0, 10.0, 10.0, 30.0, 30.0, "assets/nope.png", absolute=False)
    with pytest.raises(ValueError):
        apply_overlay(pdf, (), (spec,), base_dir=tmp_path, output=tmp_path / "o.pdf")


def test_image_out_of_range_page_raises(
    tmp_path: Path, make_pdf: MakePdf, make_image: MakeImage
) -> None:
    pdf = make_pdf([(300, 400)])
    img = make_image("png")
    spec = ImageFieldSpec(5, 10.0, 10.0, 30.0, 30.0, str(img), absolute=True)
    with pytest.raises(ValueError):
        apply_overlay(pdf, (), (spec,), base_dir=tmp_path, output=tmp_path / "o.pdf")
