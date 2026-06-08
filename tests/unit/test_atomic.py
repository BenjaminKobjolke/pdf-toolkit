"""Unit tests for app.pdf._atomic.write_pdf_atomic."""

from __future__ import annotations

import os
import stat
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from app.pdf._atomic import write_pdf_atomic
from tests.conftest import MakePdf


def _writer_with(pages: int) -> PdfWriter:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=100, height=200)
    return writer


def test_write_pdf_atomic_overwrites_readonly_source(make_pdf: MakePdf) -> None:
    source = make_pdf([(10, 10)])
    os.chmod(source, stat.S_IREAD)  # email/download PDFs arrive read-only -> WinError 5

    write_pdf_atomic(source, _writer_with(3))

    assert len(PdfReader(str(source)).pages) == 3


def test_write_pdf_atomic_leaves_no_tmp(make_pdf: MakePdf) -> None:
    source = make_pdf([(10, 10)])

    write_pdf_atomic(source, _writer_with(1))

    assert list(Path(source.parent).glob("*.tmp")) == []
