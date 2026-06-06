"""Unit tests for app.pdf.extractor."""

from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfWriter

from app.pdf.extractor import default_extract_dest, extract_page
from tests.conftest import MakePdf, PageSizesOf


def test_extract_writes_single_page(
    make_pdf: MakePdf, page_sizes_of: PageSizesOf, tmp_path: Path
) -> None:
    source = make_pdf([(10, 10), (20, 20), (30, 30)], name="doc.pdf")
    dest = tmp_path / "out.pdf"

    extract_page(source, page=2, dest=dest)

    assert page_sizes_of(dest) == [(20, 20)]


def test_extract_leaves_original_untouched(make_pdf: MakePdf, tmp_path: Path) -> None:
    source = make_pdf([(10, 10), (20, 20), (30, 30)], name="doc.pdf")
    before = source.read_bytes()
    dest = tmp_path / "out.pdf"

    extract_page(source, page=2, dest=dest)

    assert source.read_bytes() == before


def test_extract_rejects_out_of_range(make_pdf: MakePdf, tmp_path: Path) -> None:
    source = make_pdf([(10, 10), (20, 20)], name="doc.pdf")
    dest = tmp_path / "out.pdf"

    with pytest.raises(ValueError, match="out of range"):
        extract_page(source, page=5, dest=dest)

    assert not dest.exists()


def test_extract_rejects_zero(make_pdf: MakePdf, tmp_path: Path) -> None:
    source = make_pdf([(10, 10), (20, 20)], name="doc.pdf")
    dest = tmp_path / "out.pdf"

    with pytest.raises(ValueError, match="1-based"):
        extract_page(source, page=0, dest=dest)


def test_extract_rejects_encrypted(tmp_path: Path) -> None:
    source = tmp_path / "encrypted.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=200)
    writer.encrypt(user_password="secret")
    with source.open("wb") as fh:
        writer.write(fh)
    dest = tmp_path / "out.pdf"

    with pytest.raises(ValueError, match="encrypted"):
        extract_page(source, page=1, dest=dest)


def test_default_extract_dest_naming() -> None:
    dest = default_extract_dest(Path("/some/dir/report.pdf"), page=3)

    assert dest == Path("/some/dir/report-p03.pdf")
