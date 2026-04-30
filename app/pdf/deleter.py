"""Delete a single page from a PDF in place."""

from __future__ import annotations

import os
from pathlib import Path

from pypdf import PdfReader, PdfWriter


def delete_page(source: Path, page_number: int) -> None:
    """Delete ``page_number`` (1-based) from ``source``, overwriting it atomically.

    Raises ``ValueError`` if the page number is < 1, exceeds the page count,
    or would leave the PDF empty.
    """
    if page_number < 1:
        raise ValueError(f"page number must be 1-based and >= 1, got {page_number}")

    reader = PdfReader(str(source))
    if reader.is_encrypted:
        raise ValueError(f"PDF is encrypted: {source}")

    total = len(reader.pages)
    if total <= 1:
        raise ValueError(
            f"refusing to delete: PDF has {total} page(s); deletion would leave it empty"
        )
    if page_number > total:
        raise ValueError(f"page {page_number} is out of range; PDF has {total} pages: {source}")

    writer = PdfWriter()
    drop_index = page_number - 1
    for index, page in enumerate(reader.pages):
        if index != drop_index:
            writer.add_page(page)

    tmp = source.with_suffix(source.suffix + ".tmp")
    with tmp.open("wb") as fh:
        writer.write(fh)
    os.replace(tmp, source)


def delete_page_range(source: Path, start_page: int, end_page: int) -> None:
    """Delete pages ``start_page``..``end_page`` (1-based, inclusive) from ``source``,
    overwriting it atomically.

    Raises ``ValueError`` if ``start_page`` < 1, ``end_page`` < ``start_page``,
    ``end_page`` exceeds the page count, the PDF is encrypted, or deletion would
    leave the PDF empty.
    """
    if start_page < 1:
        raise ValueError(f"start page must be 1-based and >= 1, got {start_page}")
    if end_page < start_page:
        raise ValueError(f"end page {end_page} must be >= start page {start_page}")

    reader = PdfReader(str(source))
    if reader.is_encrypted:
        raise ValueError(f"PDF is encrypted: {source}")

    total = len(reader.pages)
    if end_page > total:
        raise ValueError(f"end page {end_page} is out of range; PDF has {total} pages: {source}")

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

    tmp = source.with_suffix(source.suffix + ".tmp")
    with tmp.open("wb") as fh:
        writer.write(fh)
    os.replace(tmp, source)
