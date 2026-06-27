"""Search-match highlight overlays for the page scene.

Owns the gold outline rects drawn over the current page. Match coordinates
arrive in PDF points and are scaled to render-time scene pixels by
``render.DEFAULT_ZOOM`` (the page's fixed logical render scale), matching where
the text/image overlay items live.
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsScene

from app.gui import render

_HIGHLIGHT_COLOR = "#ffd000"  # gold outline for search matches
_HIGHLIGHT_Z = 2.0  # above the page (0) and overlay items (1)


class PageHighlights:
    """Draws and clears search-match outlines on a scene."""

    def __init__(self, scene: QGraphicsScene) -> None:
        self._scene = scene
        self._items: list[QGraphicsRectItem] = []
        self._rects_pts: list[tuple[float, float, float, float]] = []

    def set(self, rects_pts: list[tuple[float, float, float, float]]) -> None:
        """Draw gold outlines for the given match rects (in PDF points)."""
        self.clear()
        self._rects_pts = list(rects_pts)
        pen = QPen(QColor(_HIGHLIGHT_COLOR))
        pen.setWidth(2)
        z = render.DEFAULT_ZOOM
        for x0, y0, x1, y1 in rects_pts:
            item = self._scene.addRect(x0 * z, y0 * z, (x1 - x0) * z, (y1 - y0) * z, pen)
            item.setZValue(_HIGHLIGHT_Z)
            self._items.append(item)

    def clear(self) -> None:
        for item in self._items:
            self._scene.removeItem(item)
        self._items.clear()
        self._rects_pts.clear()

    def rects_points(self) -> list[tuple[float, float, float, float]]:
        """Return the current match rects in PDF points (empty when cleared)."""
        return list(self._rects_pts)

    def has(self) -> bool:
        return bool(self._items)

    def items(self) -> tuple[QGraphicsRectItem, ...]:
        return tuple(self._items)
