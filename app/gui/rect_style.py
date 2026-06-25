"""The Qt <-> spec mapping for placed rectangles.

Keeps ``QColor`` conversion out of both the pure DTO (``rect_spec``) and the
controller, mirroring ``text_style`` / ``image_style``.
"""

from __future__ import annotations

from PySide6.QtGui import QColor

from app.gui.rect_item import RectItem
from app.pdf.rect_spec import RectFieldSpec

DEFAULT_FILL = "#ffe066"  # a soft yellow highlight, distinct from black text
DEFAULT_SIZE = (160.0, 90.0)


def item_to_spec(item: RectItem, page_index: int) -> RectFieldSpec:
    return RectFieldSpec(
        page_index=page_index,
        x=item.pos().x(),
        y=item.pos().y(),
        width=item.current_width(),
        height=item.current_height(),
        color=item.fill_color().name(QColor.NameFormat.HexRgb),
        z=item.zValue(),
    )


def spec_to_item(spec: RectFieldSpec) -> RectItem:
    item = RectItem(spec.width, spec.height, spec.color)
    item.setPos(spec.x, spec.y)
    item.setZValue(spec.z)
    return item


def build_item(width: float, height: float, color: str) -> RectItem:
    """Create a :class:`RectItem` at the origin with the given size and fill."""
    return RectItem(width, height, color)
