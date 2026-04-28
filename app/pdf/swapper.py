"""Swap the two pages of a 2-page PDF in place."""

from __future__ import annotations

import os
from pathlib import Path

from pypdf import PdfReader, PdfWriter


def swap_two_pages(source: Path) -> None:
    """Swap pages of a 2-page PDF, overwriting ``source`` atomically.

    Raises ``ValueError`` if the PDF is encrypted or does not have exactly 2 pages.
    """
    reader = PdfReader(str(source))
    if reader.is_encrypted:
        raise ValueError(f"PDF is encrypted: {source}")
    if len(reader.pages) != 2:
        raise ValueError(f"swap requires exactly 2 pages, got {len(reader.pages)}: {source}")

    writer = PdfWriter()
    writer.add_page(reader.pages[1])
    writer.add_page(reader.pages[0])

    tmp = source.with_suffix(source.suffix + ".tmp")
    with tmp.open("wb") as fh:
        writer.write(fh)
    os.replace(tmp, source)
