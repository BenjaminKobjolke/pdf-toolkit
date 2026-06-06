"""Unit tests for app.pdf.mover."""

from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfWriter

from app.pdf.mover import move_page
from tests.conftest import MakePdf, PageSizesOf


def test_move_forward(make_pdf: MakePdf, page_sizes_of: PageSizesOf) -> None:
    source = make_pdf([(10, 10), (20, 20), (30, 30), (40, 40)])

    move_page(source, from_page=1, to_page=3)

    assert page_sizes_of(source) == [(20, 20), (30, 30), (10, 10), (40, 40)]


def test_move_backward(make_pdf: MakePdf, page_sizes_of: PageSizesOf) -> None:
    source = make_pdf([(10, 10), (20, 20), (30, 30), (40, 40)])

    move_page(source, from_page=4, to_page=2)

    assert page_sizes_of(source) == [(10, 10), (40, 40), (20, 20), (30, 30)]


def test_move_to_first(make_pdf: MakePdf, page_sizes_of: PageSizesOf) -> None:
    source = make_pdf([(10, 10), (20, 20), (30, 30)])

    move_page(source, from_page=3, to_page=1)

    assert page_sizes_of(source) == [(30, 30), (10, 10), (20, 20)]


def test_move_to_last(make_pdf: MakePdf, page_sizes_of: PageSizesOf) -> None:
    source = make_pdf([(10, 10), (20, 20), (30, 30)])

    move_page(source, from_page=1, to_page=3)

    assert page_sizes_of(source) == [(20, 20), (30, 30), (10, 10)]


def test_move_same_position_is_noop(make_pdf: MakePdf) -> None:
    source = make_pdf([(10, 10), (20, 20), (30, 30)])
    original_bytes = source.read_bytes()

    move_page(source, from_page=2, to_page=2)

    assert source.read_bytes() == original_bytes


def test_move_rejects_from_out_of_range(make_pdf: MakePdf) -> None:
    source = make_pdf([(10, 10), (20, 20)])
    original_bytes = source.read_bytes()

    with pytest.raises(ValueError, match="out of range"):
        move_page(source, from_page=3, to_page=1)

    assert source.read_bytes() == original_bytes


def test_move_rejects_to_out_of_range(make_pdf: MakePdf) -> None:
    source = make_pdf([(10, 10), (20, 20)])
    original_bytes = source.read_bytes()

    with pytest.raises(ValueError, match="out of range"):
        move_page(source, from_page=1, to_page=5)

    assert source.read_bytes() == original_bytes


def test_move_rejects_zero(make_pdf: MakePdf) -> None:
    source = make_pdf([(10, 10), (20, 20)])
    original_bytes = source.read_bytes()

    with pytest.raises(ValueError, match="1-based"):
        move_page(source, from_page=0, to_page=1)

    assert source.read_bytes() == original_bytes


def test_move_rejects_encrypted_pdf(tmp_path: Path) -> None:
    source = tmp_path / "encrypted.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=200)
    writer.add_blank_page(width=300, height=400)
    writer.encrypt(user_password="secret")
    with source.open("wb") as fh:
        writer.write(fh)

    with pytest.raises(ValueError, match="encrypted"):
        move_page(source, from_page=1, to_page=2)
