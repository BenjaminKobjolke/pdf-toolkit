"""Clipboard view-grab helpers for :class:`~app.gui.page_view.PageView`.

The viewport grab clipped to the visible page area — what the "Copy current
view to clipboard" commands put on the clipboard. Split out so ``page_view``
stays under the file-length cap. Plain functions, not a mixin: a mixin would
have to subclass ``QGraphicsView`` for these calls, and shiboken aborts on
that diamond inheritance.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QRect
from PySide6.QtGui import QPixmap

if TYPE_CHECKING:
    from app.gui.page_view import PageView


def visible_page_rect(view: PageView) -> QRect:
    """Page area currently visible, in viewport logical coords (empty if no doc).

    Guarded by the source, not the scene rect — the no-doc placeholder gives
    the scene a non-empty rect, and ``reset()`` leaves the last page's scene
    rect behind.
    """
    if view.source() is None:
        return QRect()
    page = view.mapFromScene(view.graphics_scene().sceneRect()).boundingRect()
    return page & view.viewport().rect()


def grab_page_area(view: PageView) -> QPixmap:
    """Grab the viewport clipped to the visible page (overlays/zoom as shown)."""
    pixmap = view.viewport().grab()
    rect = visible_page_rect(view)
    if rect.isEmpty():
        return pixmap  # ponytail: fallback to full grab when no page is visible
    dpr = pixmap.devicePixelRatio()
    x, y = round(rect.x() * dpr), round(rect.y() * dpr)
    w, h = round(rect.width() * dpr), round(rect.height() * dpr)
    return pixmap.copy(QRect(x, y, w, h))
