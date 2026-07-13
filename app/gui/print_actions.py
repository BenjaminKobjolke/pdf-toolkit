"""Print the open document via the standard OS print dialog.

Renders each page of the working copy with PyMuPDF (same idiom as
:mod:`app.gui.render`) and paints it onto the user-chosen ``QPrinter``. Kept as
a thin collaborator so :meth:`PrintActions.render_to_printer` can be exercised
against a PDF-output printer without showing a dialog.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import fitz  # PyMuPDF
from PySide6.QtCore import QRectF
from PySide6.QtGui import QImage, QPainter
from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog
from PySide6.QtWidgets import QWidget

from app.pdf.file_format import open_fitz

_POINTS_PER_INCH: float = 72.0
_RGB_FORMAT = QImage.Format.Format_RGB888


class PrintActions:
    """Show the print dialog and rasterise the open PDF onto the printer."""

    def __init__(self, parent: QWidget, source: Callable[[], Path | None]) -> None:
        self._parent = parent
        self._source = source  # the working copy on disk (None when no document)

    def print_document(self) -> None:
        """Show a print preview of the working copy; its Print button uses the OS dialog.

        ``QPrintPreviewDialog`` renders the preview via ``paintRequested`` and, on its
        Print button, opens the standard ``QPrintDialog`` for printer selection.
        """
        source = self._source()
        if source is None:
            return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintPreviewDialog(printer, self._parent)
        dialog.paintRequested.connect(lambda p: self.render_to_printer(source, p))
        dialog.exec()

    def render_to_printer(self, source: Path, printer: QPrinter) -> None:
        """Paint every page of ``source`` onto ``printer`` at its device resolution.

        Separated from :meth:`print_document` so tests can drive a PDF-output
        ``QPrinter`` without a dialog.
        """
        scale = printer.resolution() / _POINTS_PER_INCH  # PDF points -> printer pixels
        doc = open_fitz(source)
        painter = QPainter()
        try:
            painter.begin(printer)
            for index in range(int(doc.page_count)):
                if index > 0:
                    printer.newPage()
                image = _render_page(doc.load_page(index), scale)
                page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
                painter.drawImage(_fit(image, page_rect), image)
        finally:
            painter.end()
            doc.close()


def _render_page(page: fitz.Page, scale: float) -> QImage:
    """Rasterise ``page`` to an RGB ``QImage`` at ``scale`` (cf. ``render.render_page``)."""
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    image = QImage(pix.samples, pix.width, pix.height, pix.stride, _RGB_FORMAT)
    # Detach from the pixmap buffer, which is freed when the page/doc closes.
    return image.copy()


def _fit(image: QImage, target: QRectF) -> QRectF:
    """Aspect-preserving rectangle that centres ``image`` inside ``target``."""
    if image.width() == 0 or image.height() == 0:
        return target
    factor = min(target.width() / image.width(), target.height() / image.height())
    width = image.width() * factor
    height = image.height() * factor
    left = target.left() + (target.width() - width) / 2
    top = target.top() + (target.height() - height) / 2
    return QRectF(left, top, width, height)
