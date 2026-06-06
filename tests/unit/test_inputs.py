"""Unit tests for app.pdf._inputs (shared path->pages helpers)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfWriter

from app.pdf._inputs import open_reader, pages_for_input
from tests.conftest import MakeImage, MakePdf


def test_open_reader_returns_reader(make_pdf: MakePdf) -> None:
    source = make_pdf([(10, 10), (20, 20)])

    reader = open_reader(source)

    assert len(reader.pages) == 2


def test_open_reader_rejects_encrypted(tmp_path: Path) -> None:
    source = tmp_path / "encrypted.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=200)
    writer.encrypt(user_password="secret")
    with source.open("wb") as fh:
        writer.write(fh)

    with pytest.raises(ValueError, match="encrypted"):
        open_reader(source)


def test_pages_for_input_pdf(make_pdf: MakePdf) -> None:
    source = make_pdf([(10, 10), (20, 20), (30, 30)])

    pages = pages_for_input(source)

    assert len(pages) == 3


def test_pages_for_input_png(make_image: MakeImage) -> None:
    image = make_image("png")

    pages = pages_for_input(image)

    assert len(pages) == 1


def test_pages_for_input_jpg(make_image: MakeImage) -> None:
    image = make_image("jpg")

    pages = pages_for_input(image)

    assert len(pages) == 1


def test_pages_for_input_rgba_png(make_image: MakeImage) -> None:
    image = make_image("rgba_png")

    pages = pages_for_input(image)

    assert len(pages) == 1


def test_pages_for_input_rejects_unsupported(tmp_path: Path) -> None:
    bogus = tmp_path / "note.txt"
    bogus.write_text("hi", encoding="utf-8")

    with pytest.raises(ValueError, match="unsupported"):
        pages_for_input(bogus)
