"""A movable, freely-resizable filled rectangle for the page scene.

Pure view object: it draws a solid fill (no border), resizes width and height
*independently* via corner handles (unlike :class:`~app.gui.image_item.ImageItem`,
which is aspect-locked), and exposes its on-page size. No PDF or persistence logic.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem

from app.gui.image_resize import CORNERS, ResizeHandleItem, anchor_point, top_left_for
from app.gui.resizable_item import ResizableItemMixin

_MIN_SIZE = 4.0


class RectItem(ResizableItemMixin, QGraphicsRectItem):
    """Drag to move, drag a corner to resize (free aspect); solid fill only."""

    def __init__(self, width: float, height: float, color: str) -> None:
        super().__init__(0.0, 0.0, max(_MIN_SIZE, width), max(_MIN_SIZE, height))
        self._color = QColor(color)
        self._editable = False
        self.setPen(Qt.PenStyle.NoPen)
        self.setBrush(QBrush(self._color))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self._handles = [ResizeHandleItem(self, corner) for corner in CORNERS]
        self._reposition_handles()
        self._set_handles_visible(False)

    # --- color -------------------------------------------------------------

    def fill_color(self) -> QColor:
        return QColor(self._color)

    def set_fill_color(self, color: QColor) -> None:
        self._color = QColor(color)
        self.setBrush(QBrush(self._color))
        self.update()

    # --- size ---------------------------------------------------------------

    def current_width(self) -> float:
        return float(self.rect().width())

    def current_height(self) -> float:
        return float(self.rect().height())

    def set_size(self, width: float, height: float) -> None:
        """Set the on-page size (top-left fixed); clamps to a minimum."""
        self.setRect(0.0, 0.0, max(_MIN_SIZE, width), max(_MIN_SIZE, height))
        self._reposition_handles()

    def resize_from_handle(self, corner: str, scene_pt: Any) -> None:
        """Resize so the dragged ``corner`` follows ``scene_pt`` (free aspect)."""
        anchor = anchor_point(corner, self.pos(), self.current_width(), self.current_height())
        new_w = max(_MIN_SIZE, abs(scene_pt.x() - anchor.x()))
        new_h = max(_MIN_SIZE, abs(scene_pt.y() - anchor.y()))
        self.setPos(top_left_for(corner, anchor, new_w, new_h))
        self.set_size(new_w, new_h)

    # --- internals (selection/handles come from ResizableItemMixin) ----------

    def _reposition_handles(self) -> None:
        rect: QRectF = self.rect()
        positions = {
            "tl": (rect.left(), rect.top()),
            "tr": (rect.right(), rect.top()),
            "bl": (rect.left(), rect.bottom()),
            "br": (rect.right(), rect.bottom()),
        }
        for handle in self._handles:
            x, y = positions[handle.corner]
            handle.setPos(x, y)
