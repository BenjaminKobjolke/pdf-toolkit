"""Delete a single page from a PDF in place."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfWriter

from app.pdf._atomic import write_pdf_atomic
from app.pdf._inputs import check_first_page, check_page_in_range, open_reader


def delete_page(source: Path, page_number: int) -> None:
    """Delete ``page_number`` (1-based) from ``source``, overwriting it atomically.

    Raises ``ValueError`` if the page number is < 1, exceeds the page count,
    or would leave the PDF empty.
    """
    check_first_page(page_number)

    reader = open_reader(source)
    total = len(reader.pages)
    if total <= 1:
        raise ValueError(
            f"refusing to delete: PDF has {total} page(s); deletion would leave it empty"
        )
    check_page_in_range(page_number, total, source)

    writer = PdfWriter()
    drop_index = page_number - 1
    for index, page in enumerate(reader.pages):
        if index != drop_index:
            writer.add_page(page)

    write_pdf_atomic(source, writer)


def delete_page_range(source: Path, start_page: int, end_page: int) -> None:
    """Delete pages ``start_page``..``end_page`` (1-based, inclusive) from ``source``,
    overwriting it atomically.

    Raises ``ValueError`` if ``start_page`` < 1, ``end_page`` < ``start_page``,
    ``end_page`` exceeds the page count, the PDF is encrypted, or deletion would
    leave the PDF empty.
    """
    check_first_page(start_page, label="start page")
    if end_page < start_page:
        raise ValueError(f"end page {end_page} must be >= start page {start_page}")

    reader = open_reader(source)
    total = len(reader.pages)
    check_page_in_range(end_page, total, source, label="end page")

    delete_count = end_page - start_page + 1
    if delete_count >= total:
        raise ValueError(
            f"refusing to delete: would leave PDF empty (deleting {delete_count} of {total} pages)"
        )

    writer = PdfWriter()
    drop_start = start_page - 1
    drop_end = end_page
    for index, page in enumerate(reader.pages):
        if index < drop_start or index >= drop_end:
            writer.add_page(page)

    write_pdf_atomic(source, writer)
