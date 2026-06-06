"""Insert pages from another PDF or an image into a PDF in place."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfWriter

from app.pdf._atomic import write_pdf_atomic
from app.pdf._inputs import open_reader, pages_for_input


def insert_after(source: Path, insert: Path, after_page: int) -> None:
    """Insert ``insert`` (a PDF or image) after ``after_page`` of ``source``.

    ``after_page`` is 1-based; ``0`` inserts before the first page. Overwrites
    ``source`` atomically. Raises ``ValueError`` if ``after_page`` is out of the
    range ``0..page_count``, ``source`` is encrypted, or ``insert`` is an
    unsupported file type.
    """
    reader = open_reader(source)
    total = len(reader.pages)
    if after_page < 0 or after_page > total:
        raise ValueError(
            f"insert position out of range; PDF has {total} pages: {after_page} in {source}"
        )

    insert_pages = pages_for_input(insert)
    existing = list(reader.pages)

    writer = PdfWriter()
    for page in existing[:after_page]:
        writer.add_page(page)
    for page in insert_pages:
        writer.add_page(page)
    for page in existing[after_page:]:
        writer.add_page(page)

    write_pdf_atomic(source, writer)
