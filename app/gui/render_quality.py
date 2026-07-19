"""Render-quality (super-sampling) control for the page view.

Keeps the page pixmap crisp at any zoom *without moving overlay coordinates*.
The pixmap's logical size is fixed at ``points x render.DEFAULT_ZOOM`` (so text
fields, images and search highlights never shift); extra sharpness comes from
rendering more *physical* pixels and tagging the image with a matching
device-pixel-ratio. Quality tracks on-screen density -- view scale x screen DPR
-- so each page is rasterised 1:1 with the pixels it actually occupies
(DPI-match), staying sharp on HiDPI displays and when zoomed in. A single-shot
timer coalesces zoom bursts into one re-render.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer
from PySide6.QtGui import QPixmap

from app.gui import render

if TYPE_CHECKING:
    from PySide6.QtWidgets import QGraphicsPixmapItem

    from app.gui.page_view import PageView

MAX_QUALITY: float = 8.0  # cap pixmap blow-up at extreme zoom
_MIN_QUALITY: float = 0.1
_RERENDER_RATIO: float = 0.15  # ignore quality changes within +/-15%
_DEBOUNCE_MS: int = 120  # coalesce rapid zoom into one re-render


def target_quality(scale: float, dpr: float) -> float:
    """Physical screen pixels per scene unit, clamped to a sane range."""
    return min(MAX_QUALITY, max(_MIN_QUALITY, scale * dpr))


def needs_rerender(current: float, target: float) -> bool:
    """True if ``target`` differs from the loaded quality enough to re-render."""
    if current <= 0.0:
        return True
    return abs(target - current) / current > _RERENDER_RATIO


class RenderQualityController:
    """Renders the page at the quality its current on-screen size deserves."""

    def __init__(self, view: PageView, pixmap_item: QGraphicsPixmapItem) -> None:
        self._view = view
        self._pixmap_item = pixmap_item
        self._quality = 0.0
        self._suspended = False
        self._timer = QTimer(view)
        self._timer.setSingleShot(True)
        self._timer.setInterval(_DEBOUNCE_MS)
        self._timer.timeout.connect(self._rerender)

    def set_suspended(self, on: bool) -> None:
        """Pause fitz re-render while a ``QMovie`` drives the pixmap directly.

        The single seam that keeps an animated GIF's frames from being clobbered
        by a static frame-0 render on load or on every zoom change.
        """
        self._suspended = on
        if on:
            self._timer.stop()

    def is_suspended(self) -> bool:
        return self._suspended

    def render_now(self) -> None:
        """Render the current page at its target quality (call on page change)."""
        if self._suspended:
            return
        self._timer.stop()
        self.render_at(self._current_target())

    def request(self, scale: float) -> None:
        """Schedule a re-render if ``scale`` now needs a different quality."""
        if self._suspended:
            return
        if needs_rerender(self._quality, target_quality(scale, self._dpr())):
            self._timer.start()

    def render_at(self, quality: float) -> bool:
        """Render the page at ``quality`` super-sampling. False if no document."""
        if self._suspended:
            return False
        source = self._view.source()
        if source is None or not Path(source).exists():
            return False
        image = render.render_page(source, self._view.current_page_index(), quality)
        self._pixmap_item.setPixmap(QPixmap.fromImage(image))
        self._quality = quality
        return True

    def _rerender(self) -> None:
        self.render_at(self._current_target())

    def _current_target(self) -> float:
        return target_quality(self._view.zoom(), self._dpr())

    def _dpr(self) -> float:
        return max(self._view.devicePixelRatioF(), 1.0)
