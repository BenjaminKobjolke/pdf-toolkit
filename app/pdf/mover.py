"""Move a single page to a new position within a PDF in place."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader, PdfWriter

from app.pdf._atomic import write_pdf_atomic


def move_page(source: Path, from_page: int, to_page: int) -> None:
    """Move ``from_page`` to position ``to_page`` (both 1-based), overwriting atomically.

    A no-op when ``from_page == to_page``. Raises ``ValueError`` if either page is
    < 1 or exceeds the page count, or the PDF is encrypted.
    """
    if from_page < 1 or to_page < 1:
        raise ValueError(f"page numbers must be 1-based and >= 1, got {from_page} -> {to_page}")

    reader = PdfReader(str(source))
    if reader.is_encrypted:
        raise ValueError(f"PDF is encrypted: {source}")

    total = len(reader.pages)
    if from_page > total or to_page > total:
        raise ValueError(
            f"page out of range; PDF has {total} pages: {from_page} -> {to_page} in {source}"
        )
    if from_page == to_page:
        return

    pages = list(reader.pages)
    moved = pages.pop(from_page - 1)
    pages.insert(to_page - 1, moved)

    writer = PdfWriter()
    for page in pages:
        writer.add_page(page)

    write_pdf_atomic(source, writer)
