"""Render PDF pages to Qt images via PyMuPDF.

Kept free of any QApplication dependency beyond constructing ``QImage`` so it
can be unit-tested in isolation (under the offscreen Qt platform).
"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF
from PySide6.QtGui import QImage

DEFAULT_ZOOM: float = 1.5
_RGB_CHANNELS: int = 3


def page_count(source: Path) -> int:
    """Return the number of pages in ``source``."""
    doc = fitz.open(source)
    try:
        return int(doc.page_count)
    finally:
        doc.close()


def render_page(source: Path, page_index: int, zoom: float = DEFAULT_ZOOM) -> QImage:
    """Render 0-based ``page_index`` of ``source`` to a ``QImage``.

    Raises ``ValueError`` if ``page_index`` is out of range.
    """
    doc = fitz.open(source)
    try:
        total = int(doc.page_count)
        if not 0 <= page_index < total:
            raise ValueError(f"page index {page_index} out of range; PDF has {total} pages")
        page = doc.load_page(page_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        image = QImage(
            pix.samples,
            pix.width,
            pix.height,
            pix.stride,
            QImage.Format.Format_RGB888,
        )
        # Detach from the pixmap's buffer, which is freed when the doc closes.
        return image.copy()
    finally:
        doc.close()
