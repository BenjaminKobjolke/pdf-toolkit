"""Unit tests for app.pdf.swapper."""

from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter

from app.pdf.swapper import swap_two_pages
from tests.conftest import MakePdf, PageSizesOf


def test_swap_reverses_two_pages(make_pdf: MakePdf, page_sizes_of: PageSizesOf) -> None:
    source = make_pdf([(100, 200), (300, 400)])
    original_sizes = page_sizes_of(source)
    assert original_sizes == [(100, 200), (300, 400)]

    swap_two_pages(source)

    assert page_sizes_of(source) == [(300, 400), (100, 200)]


def test_swap_rejects_single_page_pdf(make_pdf: MakePdf) -> None:
    source = make_pdf([(100, 200)])
    original_bytes = source.read_bytes()

    with pytest.raises(ValueError, match="exactly 2 pages"):
        swap_two_pages(source)

    assert source.read_bytes() == original_bytes


def test_swap_rejects_three_page_pdf(make_pdf: MakePdf) -> None:
    source = make_pdf([(100, 200), (300, 400), (500, 600)])
    original_bytes = source.read_bytes()

    with pytest.raises(ValueError, match="exactly 2 pages"):
        swap_two_pages(source)

    assert source.read_bytes() == original_bytes


def test_swap_rejects_encrypted_pdf(tmp_path: Path) -> None:
    source = tmp_path / "encrypted.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=200)
    writer.add_blank_page(width=300, height=400)
    writer.encrypt(user_password="secret")
    with source.open("wb") as fh:
        writer.write(fh)

    with pytest.raises(ValueError, match="encrypted"):
        swap_two_pages(source)


def test_swap_overwrites_in_place(make_pdf: MakePdf) -> None:
    source = make_pdf([(100, 200), (300, 400)], name="target.pdf")
    path_before = source

    swap_two_pages(source)

    assert path_before.exists()
    assert path_before.name == "target.pdf"
    assert len(PdfReader(str(path_before)).pages) == 2
