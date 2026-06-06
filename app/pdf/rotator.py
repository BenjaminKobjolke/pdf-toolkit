"""Rotate a single page of a PDF in place."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader, PdfWriter

from app.pdf._atomic import write_pdf_atomic

# Rotation amounts in clockwise degrees. "Left" is a quarter-turn
# anticlockwise, i.e. 270 clockwise; pypdf normalizes the stored angle.
ROTATE_RIGHT = 90
ROTATE_LEFT = 270
ROTATE_FLIP = 180


def rotate_page(source: Path, page_number: int, degrees: int) -> None:
    """Rotate ``page_number`` (1-based) by ``degrees`` clockwise, overwriting atomically.

    Raises ``ValueError`` if ``degrees`` is not a multiple of 90, the page number
    is < 1 or exceeds the page count, or the PDF is encrypted.
    """
    if degrees % 90 != 0:
        raise ValueError(f"rotation must be a multiple of 90, got {degrees}")
    if page_number < 1:
        raise ValueError(f"page number must be 1-based and >= 1, got {page_number}")

    reader = PdfReader(str(source))
    if reader.is_encrypted:
        raise ValueError(f"PDF is encrypted: {source}")

    total = len(reader.pages)
    if page_number > total:
        raise ValueError(f"page {page_number} is out of range; PDF has {total} pages: {source}")

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.pages[page_number - 1].rotate(degrees)

    write_pdf_atomic(source, writer)
