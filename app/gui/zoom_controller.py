"""View-transform zoom for the page view, with a remembered mode.

The page is rendered at a fixed ``render.DEFAULT_ZOOM``; zoom is then a
``QGraphicsView`` transform on top, so text-field scene coordinates and the
sidecar are untouched. The *mode* is remembered so it re-applies on page
changes: ``fit`` re-fits each page (sizes can differ), ``scaled`` holds a fixed
factor (100% and manual in/out).
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtGui import QTransform
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsView

from app.config.zoom_settings import ZoomSettings
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

    def __init__(
        self,
        view: QGraphicsView,
        pixmap_item: QGraphicsPixmapItem,
        on_scale_changed: Callable[[float], None] | None = None,
    ) -> None:
        self._view = view
        self._pixmap_item = pixmap_item
        self._zoom = _ZOOM_ACTUAL
        self._mode = _MODE_SCALED
        self._on_scale_changed = on_scale_changed

    def zoom(self) -> float:
        """Return the current scene-to-view scale factor."""
        return self._zoom

    def percent(self) -> int:
        """Current zoom as a user-facing percentage (100 = true PDF size)."""
        return round(self._zoom / _ZOOM_ACTUAL * 100)

    def current_default(self) -> ZoomSettings:
        """Current zoom expressed as a remembered default (fit vs. percentage)."""
        return ZoomSettings(fit=self._mode == _MODE_FIT, percent=self.percent())

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

    def set_default(self, fit: bool, percent: int) -> None:
        """Set the remembered start mode without applying it (safe before load).

        ``reapply`` (called on every page render) then realises it: ``fit``
        re-fits each page, ``scaled`` holds ``percent`` of true PDF size.
        """
        if fit:
            self._mode = _MODE_FIT
        else:
            self._mode = _MODE_SCALED
            self._zoom = (percent / 100.0) * _ZOOM_ACTUAL

    def reapply(self) -> None:
        """Re-apply the current zoom mode after a page render."""
        if self._mode == _MODE_FIT:
            self._fit_to_viewport()
        else:
            self._apply(self._zoom)

    def _apply(self, scale: float) -> None:
        self._zoom = scale
        self._view.setTransform(QTransform().scale(scale, scale))
        self._notify()

    def _fit_to_viewport(self) -> None:
        # Compute the fit scale directly instead of using ``fitInView``, whose
        # result drifts with the current scrollbar/frame state (so it isn't
        # idempotent and mis-fits on page change). ``maximumViewportSize`` is the
        # viewport size as if no scrollbars are shown -- a stable basis.
        rect = self._pixmap_item.boundingRect()
        if rect.width() <= 0 or rect.height() <= 0:
            return
        avail = self._view.maximumViewportSize()
        scale = min(avail.width() / rect.width(), avail.height() / rect.height())
        self._apply(scale)

    def _notify(self) -> None:
        if self._on_scale_changed is not None:
            self._on_scale_changed(self._zoom)
