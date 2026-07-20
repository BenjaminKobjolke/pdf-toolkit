"""Render PDF pages to Qt images via PyMuPDF.

Kept free of any QApplication dependency beyond constructing ``QImage`` so it
can be unit-tested in isolation (under the offscreen Qt platform).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF
from PySide6.QtGui import QBrush, QColor, QImage, QPainter

from app.config.image_background_settings import ImageBackground, ImageBackgroundSettings
from app.pdf.file_format import IMAGE_FORMATS, FileFormat, open_fitz

DEFAULT_ZOOM: float = 1.5
_RGB_CHANNELS: int = 3

_SOLID_COLORS: dict[ImageBackground, str] = {
    ImageBackground.WHITE: "#FFFFFF",
    ImageBackground.BLACK: "#000000",
    ImageBackground.GREEN: "#00FF00",
    ImageBackground.BLUE: "#0000FF",
}
_CHECKER_SQUARE_PX = 8
_CHECKER_LIGHT = "#FFFFFF"
_CHECKER_DARK = "#CCCCCC"

# ponytail: single-window viewer, so one module-level setting is enough (same
# pattern as file_format's text settings). Defaults keep non-GUI callers on the
# historical white flatten without any wiring.
_active_image_background = ImageBackgroundSettings()


def set_image_background(settings: ImageBackgroundSettings) -> None:
    """Set the backdrop applied behind transparent image documents."""
    global _active_image_background
    _active_image_background = settings


def active_image_background() -> ImageBackground:
    """The backdrop currently applied by :func:`render_page` for images."""
    return _active_image_background.background


def _checker_tile() -> QImage:
    tile = QImage(_CHECKER_SQUARE_PX * 2, _CHECKER_SQUARE_PX * 2, QImage.Format.Format_RGB32)
    tile.fill(QColor(_CHECKER_LIGHT))
    painter = QPainter(tile)
    dark = QColor(_CHECKER_DARK)
    painter.fillRect(_CHECKER_SQUARE_PX, 0, _CHECKER_SQUARE_PX, _CHECKER_SQUARE_PX, dark)
    painter.fillRect(0, _CHECKER_SQUARE_PX, _CHECKER_SQUARE_PX, _CHECKER_SQUARE_PX, dark)
    painter.end()
    return tile


def compose(image: QImage, background: ImageBackground) -> QImage:
    """Flatten ``image``'s alpha onto ``background`` (same size, opaque RGB)."""
    result = QImage(image.size(), QImage.Format.Format_RGB32)
    painter = QPainter(result)
    if background is ImageBackground.CHECKER:
        painter.fillRect(result.rect(), QBrush(_checker_tile()))
    else:
        painter.fillRect(result.rect(), QColor(_SOLID_COLORS[background]))
    painter.drawImage(0, 0, image)
    painter.end()
    result.setDevicePixelRatio(image.devicePixelRatio())
    return result


@dataclass(frozen=True)
class DocMetadata:
    """The document metadata fields the viewer surfaces (empty string when unset)."""

    title: str = ""
    author: str = ""
    subject: str = ""
    keywords: str = ""
    creator: str = ""
    producer: str = ""


def page_count(source: Path) -> int:
    """Return the number of pages in ``source``."""
    doc = open_fitz(source)
    try:
        return int(doc.page_count)
    finally:
        doc.close()


def page_size(source: Path, page_index: int) -> tuple[float, float]:
    """Return the (width, height) of 0-based ``page_index`` in PDF points.

    For image documents fitz reports the pixel dimensions as the page rect.
    """
    doc = open_fitz(source)
    try:
        rect = doc.load_page(page_index).rect
        return (float(rect.width), float(rect.height))
    finally:
        doc.close()


def doc_metadata(source: Path) -> DocMetadata:
    """Read ``source``'s document metadata into a typed value (missing → "")."""
    doc = open_fitz(source)
    try:
        meta = doc.metadata or {}
    finally:
        doc.close()
    return DocMetadata(
        title=meta.get("title") or "",
        author=meta.get("author") or "",
        subject=meta.get("subject") or "",
        keywords=meta.get("keywords") or "",
        creator=meta.get("creator") or "",
        producer=meta.get("producer") or "",
    )


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
    doc = open_fitz(source)
    try:
        total = int(doc.page_count)
        if not 0 <= page_index < total:
            raise ValueError(f"page index {page_index} out of range; PDF has {total} pages")
        page = doc.load_page(page_index)
        scale = zoom * quality
        use_background = FileFormat.of(source) in IMAGE_FORMATS
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=use_background)
        if use_background:
            rgba = QImage(
                pix.samples,
                pix.width,
                pix.height,
                pix.stride,
                QImage.Format.Format_RGBA8888,
            )
            # compose() allocates a fresh image, so no detach copy is needed.
            image = compose(rgba, active_image_background())
            image.setDevicePixelRatio(quality)
            return image
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
