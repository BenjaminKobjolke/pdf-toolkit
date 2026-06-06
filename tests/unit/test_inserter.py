"""Unit tests for app.pdf.inserter."""

from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter

from app.pdf.inserter import insert_after
from tests.conftest import MakeImage, MakePdf, PageSizesOf


def test_insert_pdf_after_page(make_pdf: MakePdf, page_sizes_of: PageSizesOf) -> None:
    source = make_pdf([(10, 10), (20, 20), (30, 30)], name="doc.pdf")
    insert = make_pdf([(99, 99)], name="ins.pdf")

    insert_after(source, insert, after_page=2)

    assert page_sizes_of(source) == [(10, 10), (20, 20), (99, 99), (30, 30)]


def test_insert_pdf_multiple_pages(make_pdf: MakePdf, page_sizes_of: PageSizesOf) -> None:
    source = make_pdf([(10, 10), (20, 20)], name="doc.pdf")
    insert = make_pdf([(88, 88), (77, 77)], name="ins.pdf")

    insert_after(source, insert, after_page=1)

    assert page_sizes_of(source) == [(10, 10), (88, 88), (77, 77), (20, 20)]


def test_insert_at_front(make_pdf: MakePdf, page_sizes_of: PageSizesOf) -> None:
    source = make_pdf([(10, 10), (20, 20)], name="doc.pdf")
    insert = make_pdf([(99, 99)], name="ins.pdf")

    insert_after(source, insert, after_page=0)

    assert page_sizes_of(source) == [(99, 99), (10, 10), (20, 20)]


def test_insert_at_end(make_pdf: MakePdf, page_sizes_of: PageSizesOf) -> None:
    source = make_pdf([(10, 10), (20, 20)], name="doc.pdf")
    insert = make_pdf([(99, 99)], name="ins.pdf")

    insert_after(source, insert, after_page=2)

    assert page_sizes_of(source) == [(10, 10), (20, 20), (99, 99)]


def test_insert_image(make_pdf: MakePdf, make_image: MakeImage) -> None:
    source = make_pdf([(10, 10), (20, 20)], name="doc.pdf")
    image = make_image("png", name="pic.png")

    insert_after(source, image, after_page=1)

    assert len(PdfReader(str(source)).pages) == 3


def test_insert_rejects_after_page_out_of_range(make_pdf: MakePdf) -> None:
    source = make_pdf([(10, 10), (20, 20)], name="doc.pdf")
    insert = make_pdf([(99, 99)], name="ins.pdf")
    before = source.read_bytes()

    with pytest.raises(ValueError, match="out of range"):
        insert_after(source, insert, after_page=5)

    assert source.read_bytes() == before


def test_insert_rejects_negative_after_page(make_pdf: MakePdf) -> None:
    source = make_pdf([(10, 10), (20, 20)], name="doc.pdf")
    insert = make_pdf([(99, 99)], name="ins.pdf")

    with pytest.raises(ValueError, match="out of range"):
        insert_after(source, insert, after_page=-1)


def test_insert_rejects_encrypted_source(tmp_path: Path, make_pdf: MakePdf) -> None:
    source = tmp_path / "encrypted.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=200)
    writer.encrypt(user_password="secret")
    with source.open("wb") as fh:
        writer.write(fh)
    insert = make_pdf([(99, 99)], name="ins.pdf")

    with pytest.raises(ValueError, match="encrypted"):
        insert_after(source, insert, after_page=1)


def test_insert_rejects_unsupported_insert_type(tmp_path: Path, make_pdf: MakePdf) -> None:
    source = make_pdf([(10, 10)], name="doc.pdf")
    bogus = tmp_path / "note.txt"
    bogus.write_text("hi", encoding="utf-8")

    with pytest.raises(ValueError, match="unsupported"):
        insert_after(source, bogus, after_page=1)
