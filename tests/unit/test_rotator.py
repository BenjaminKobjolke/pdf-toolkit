"""Unit tests for app.pdf.rotator."""

from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter

from app.pdf.rotator import ROTATE_FLIP, ROTATE_LEFT, ROTATE_RIGHT, rotate_page
from tests.conftest import MakePdf, PageSizesOf


def _rotations(pdf: Path) -> list[int]:
    return [page.rotation for page in PdfReader(str(pdf)).pages]


def test_rotate_right_sets_90(make_pdf: MakePdf) -> None:
    source = make_pdf([(100, 200), (300, 400)])

    rotate_page(source, page_number=1, degrees=ROTATE_RIGHT)

    assert _rotations(source) == [90, 0]


def test_rotate_left_sets_270(make_pdf: MakePdf) -> None:
    source = make_pdf([(100, 200), (300, 400)])

    rotate_page(source, page_number=2, degrees=ROTATE_LEFT)

    assert _rotations(source) == [0, 270]


def test_rotate_180(make_pdf: MakePdf) -> None:
    source = make_pdf([(100, 200)])

    rotate_page(source, page_number=1, degrees=ROTATE_FLIP)

    assert _rotations(source) == [180]


def test_rotate_preserves_page_count_and_sizes(
    make_pdf: MakePdf, page_sizes_of: PageSizesOf
) -> None:
    source = make_pdf([(100, 200), (300, 400), (500, 600)])

    rotate_page(source, page_number=2, degrees=ROTATE_RIGHT)

    assert page_sizes_of(source) == [(100, 200), (300, 400), (500, 600)]


def test_rotate_rejects_non_multiple_of_90(make_pdf: MakePdf) -> None:
    source = make_pdf([(100, 200)])
    original_bytes = source.read_bytes()

    with pytest.raises(ValueError, match="multiple of 90"):
        rotate_page(source, page_number=1, degrees=45)

    assert source.read_bytes() == original_bytes


def test_rotate_rejects_zero_page(make_pdf: MakePdf) -> None:
    source = make_pdf([(100, 200), (300, 400)])
    original_bytes = source.read_bytes()

    with pytest.raises(ValueError, match="1-based"):
        rotate_page(source, page_number=0, degrees=ROTATE_RIGHT)

    assert source.read_bytes() == original_bytes


def test_rotate_rejects_out_of_range(make_pdf: MakePdf) -> None:
    source = make_pdf([(100, 200), (300, 400)])
    original_bytes = source.read_bytes()

    with pytest.raises(ValueError, match="out of range"):
        rotate_page(source, page_number=3, degrees=ROTATE_RIGHT)

    assert source.read_bytes() == original_bytes


def test_rotate_rejects_encrypted_pdf(tmp_path: Path) -> None:
    source = tmp_path / "encrypted.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=200)
    writer.encrypt(user_password="secret")
    with source.open("wb") as fh:
        writer.write(fh)

    with pytest.raises(ValueError, match="encrypted"):
        rotate_page(source, page_number=1, degrees=ROTATE_RIGHT)
