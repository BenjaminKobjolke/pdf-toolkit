"""A red crosshair marker for custom text-field placement.

Drawn on top of everything while the user picks a spot. It ignores the view
transform so it stays a constant on-screen size at any zoom; its scene position
is the point it marks (the cross centre).
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget

_ARM = 12.0  # half-length of each cross stroke, in screen pixels
_COLOR = "#ff0000"
_PEN_WIDTH = 2
_Z = 3.0  # above the page (0), text items (1) and search highlights (2)


class CrosshairItem(QGraphicsItem):
    """A constant-size red ``+`` marking the spot a new field will land."""

    def __init__(self) -> None:
        super().__init__()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, True)
        self.setZValue(_Z)

    def boundingRect(self) -> QRectF:
        return QRectF(-_ARM, -_ARM, 2 * _ARM, 2 * _ARM)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        pen = QPen(QColor(_COLOR))
        pen.setWidth(_PEN_WIDTH)
        painter.setPen(pen)
        painter.drawLine(QPointF(-_ARM, 0.0), QPointF(_ARM, 0.0))
        painter.drawLine(QPointF(0.0, -_ARM), QPointF(0.0, _ARM))
