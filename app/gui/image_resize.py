"""Corner resize handles for a placed image.

Four small squares drawn at the image corners while it is selected in edit mode.
Dragging a handle scales the image uniformly (aspect-ratio locked), keeping the
opposite corner anchored. Handles ignore the view transform so they stay a
constant on-screen size at any zoom.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsSceneMouseEvent

if TYPE_CHECKING:
    from app.gui.image_item import ImageItem

HANDLE_SIZE = 9.0
_HALF = HANDLE_SIZE / 2.0
_HANDLE_COLOR = "#1e88e5"
_HANDLE_Z = 3.0

# Corner ids and which edges they touch (used to pick the anchored opposite corner).
CORNERS = ("tl", "tr", "bl", "br")


def is_right(corner: str) -> bool:
    return corner in ("tr", "br")


def is_bottom(corner: str) -> bool:
    return corner in ("bl", "br")


class ResizeHandleItem(QGraphicsRectItem):
    """One corner grab handle; drags resize its parent :class:`ImageItem`."""

    def __init__(self, image: ImageItem, corner: str) -> None:
        super().__init__(-_HALF, -_HALF, HANDLE_SIZE, HANDLE_SIZE, parent=image)
        self._image = image
        self._corner = corner
        self.setBrush(QBrush(QColor(_HANDLE_COLOR)))
        self.setPen(QColor("#ffffff"))
        self.setZValue(_HANDLE_Z)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, True)
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)

    @property
    def corner(self) -> str:
        return self._corner

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        event.accept()  # swallow so the parent image does not start moving

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self._image.resize_from_handle(self._corner, event.scenePos())
        event.accept()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        event.accept()


def anchor_point(corner: str, top_left: QPointF, width: float, height: float) -> QPointF:
    """Return the opposite-corner scene point that stays fixed during a drag."""
    ax = top_left.x() if is_right(corner) else top_left.x() + width
    ay = top_left.y() if is_bottom(corner) else top_left.y() + height
    return QPointF(ax, ay)


def top_left_for(corner: str, anchor: QPointF, new_width: float, new_height: float) -> QPointF:
    """Return the new top-left so ``anchor`` (the opposite corner) stays put."""
    left = anchor.x() if is_right(corner) else anchor.x() - new_width
    top = anchor.y() if is_bottom(corner) else anchor.y() - new_height
    return QPointF(left, top)
