"""Unit tests for RectItem free resize and the rect_style bridge (offscreen Qt)."""

from __future__ import annotations

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsItem

from app.gui import rect_style
from app.gui.rect_item import RectItem
from app.pdf.rect_spec import RectFieldSpec


def test_set_size_clamps_to_minimum(qapp: object) -> None:
    item = RectItem(100.0, 50.0, "#ff0000")
    item.set_size(0.0, 0.0)
    assert item.current_width() >= 1.0
    assert item.current_height() >= 1.0


def test_free_resize_independent_dimensions(qapp: object) -> None:
    item = RectItem(100.0, 50.0, "#ff0000")
    item.setPos(0.0, 0.0)
    # Drag the bottom-right corner to (40, 200): width shrinks, height grows,
    # independently — proving it is NOT aspect-locked like an image.
    item.resize_from_handle("br", QPointF(40.0, 200.0))
    assert item.current_width() == 40.0
    assert item.current_height() == 200.0


def test_resize_keeps_opposite_corner_anchored(qapp: object) -> None:
    item = RectItem(100.0, 100.0, "#ff0000")
    item.setPos(50.0, 50.0)  # tl=(50,50), br=(150,150)
    # Drag the top-left corner; the bottom-right (150,150) must stay put.
    item.resize_from_handle("tl", QPointF(80.0, 90.0))
    assert (item.pos().x(), item.pos().y()) == (80.0, 90.0)
    assert item.pos().x() + item.current_width() == 150.0
    assert item.pos().y() + item.current_height() == 150.0


def test_set_editable_toggles_flags(qapp: object) -> None:
    item = RectItem(40.0, 40.0, "#00ff00")
    item.set_editable(True)
    assert item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable
    item.setSelected(True)
    item.set_editable(False)
    assert not item.isSelected()


def test_item_spec_round_trip(qapp: object) -> None:
    item = rect_style.build_item(120.0, 60.0, "#123456")
    item.setPos(7.0, 8.0)
    item.setZValue(4.0)
    spec = rect_style.item_to_spec(item, 2)
    assert spec == RectFieldSpec(2, 7.0, 8.0, 120.0, 60.0, "#123456", 4.0)
    back = rect_style.spec_to_item(spec)
    assert (back.pos().x(), back.pos().y()) == (7.0, 8.0)
    assert back.zValue() == 4.0
    assert back.fill_color().name() == "#123456"
