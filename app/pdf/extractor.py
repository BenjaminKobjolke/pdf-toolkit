"""Extract a single page of a PDF into its own new file."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfWriter

from app.pdf._atomic import write_pdf_atomic
from app.pdf._inputs import check_first_page, check_page_in_range, open_reader


def default_extract_dest(source: Path, page: int) -> Path:
    """Return the default destination ``<stem>-pNN<suffix>`` beside ``source``."""
    return source.with_name(f"{source.stem}-p{page:02d}{source.suffix}")


def extract_page(source: Path, page: int, dest: Path) -> None:
    """Write ``page`` (1-based) of ``source`` to ``dest``, leaving ``source`` untouched.

    Raises ``ValueError`` if ``page`` is < 1, exceeds the page count, or
    ``source`` is encrypted.
    """
    check_first_page(page)

    reader = open_reader(source)
    check_page_in_range(page, len(reader.pages), source)

    writer = PdfWriter()
    writer.add_page(reader.pages[page - 1])
    write_pdf_atomic(dest, writer)
