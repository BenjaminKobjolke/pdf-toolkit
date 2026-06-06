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


def render_page(
    source: Path,
    page_index: int,
    quality: float = 1.0,
    zoom: float = DEFAULT_ZOOM,
) -> QImage:
    """Render 0-based ``page_index`` of ``source`` to a ``QImage``.

    ``quality`` is a super-sampling factor: the page is rasterised at
    ``zoom * quality`` physical pixels but tagged with a device-pixel-ratio of
    ``quality`` so its *logical* (device-independent) size stays ``zoom``-scaled.
    More pixels for sharpness, identical scene coordinates (``quality == 1.0``
    reproduces a plain ``zoom`` render). Raises ``ValueError`` if ``page_index``
    is out of range.
    """
    doc = fitz.open(source)
    try:
        total = int(doc.page_count)
        if not 0 <= page_index < total:
            raise ValueError(f"page index {page_index} out of range; PDF has {total} pages")
        page = doc.load_page(page_index)
        scale = zoom * quality
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        image = QImage(
            pix.samples,
            pix.width,
            pix.height,
            pix.stride,
            QImage.Format.Format_RGB888,
        )
        image.setDevicePixelRatio(quality)
        # Detach from the pixmap's buffer, which is freed when the doc closes.
        return image.copy()
    finally:
        doc.close()
