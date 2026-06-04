"""View-transform zoom for the page view, with a remembered mode.

The page is rendered at a fixed ``render.DEFAULT_ZOOM``; zoom is then a
``QGraphicsView`` transform on top, so text-field scene coordinates and the
sidecar are untouched. The *mode* is remembered so it re-applies on page
changes: ``fit`` re-fits each page (sizes can differ), ``scaled`` holds a fixed
factor (100% and manual in/out).
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QTransform
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsView

from app.gui import render

_ZOOM_IN_FACTOR = 1.1  # zoom in 10%
_ZOOM_OUT_FACTOR = 0.9  # zoom out 10%
# "100%" = true PDF size: the page is rendered at render.DEFAULT_ZOOM, so the
# view transform must divide that back out.
_ZOOM_ACTUAL = 1.0 / render.DEFAULT_ZOOM

_MODE_FIT = "fit"
_MODE_SCALED = "scaled"


class ZoomController:
    """Owns the page view's zoom factor + mode and applies it as a transform."""

    def __init__(self, view: QGraphicsView, pixmap_item: QGraphicsPixmapItem) -> None:
        self._view = view
        self._pixmap_item = pixmap_item
        self._zoom = _ZOOM_ACTUAL
        self._mode = _MODE_SCALED

    def zoom(self) -> float:
        """Return the current scene-to-view scale factor."""
        return self._zoom

    def actual(self) -> None:
        """Show the page at true PDF size (100%); stays 100% on page changes."""
        self._mode = _MODE_SCALED
        self._apply(_ZOOM_ACTUAL)

    def zoom_in(self) -> None:
        self._mode = _MODE_SCALED
        self._apply(self._zoom * _ZOOM_IN_FACTOR)

    def zoom_out(self) -> None:
        self._mode = _MODE_SCALED
        self._apply(self._zoom * _ZOOM_OUT_FACTOR)

    def fit(self) -> None:
        """Fit the page to the viewport; re-fits each page as you navigate."""
        self._mode = _MODE_FIT
        self._fit_to_viewport()

    def reapply(self) -> None:
        """Re-apply the current zoom mode after a page render."""
        if self._mode == _MODE_FIT:
            self._fit_to_viewport()
        else:
            self._apply(self._zoom)

    def _apply(self, scale: float) -> None:
        self._zoom = scale
        self._view.setTransform(QTransform().scale(scale, scale))

    def _fit_to_viewport(self) -> None:
        self._view.fitInView(self._pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        self._zoom = self._view.transform().m11()
