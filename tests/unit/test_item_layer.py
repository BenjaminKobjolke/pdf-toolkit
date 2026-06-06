"""Unit tests for the generic ItemLayer (offscreen Qt)."""

from __future__ import annotations

from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsScene

from app.gui.item_layer import ItemLayer


def _rect(selectable: bool = False) -> QGraphicsRectItem:
    item = QGraphicsRectItem(0, 0, 10, 10)
    if selectable:
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
    return item


def test_add_sets_z_and_tracks(qapp: object) -> None:
    scene = QGraphicsScene()
    layer: ItemLayer[QGraphicsRectItem] = ItemLayer(scene, 1.0)
    a, b = _rect(), _rect()
    layer.add(a)
    layer.add(b)
    assert layer.items() == (a, b)
    assert a.zValue() == 1.0


def test_remove_and_clear(qapp: object) -> None:
    scene = QGraphicsScene()
    layer: ItemLayer[QGraphicsRectItem] = ItemLayer(scene, 1.0)
    a, b = _rect(), _rect()
    layer.add(a)
    layer.add(b)
    layer.remove(a)
    assert layer.items() == (b,)
    layer.clear()
    assert layer.items() == ()


def test_selected_returns_first_selected(qapp: object) -> None:
    scene = QGraphicsScene()
    layer: ItemLayer[QGraphicsRectItem] = ItemLayer(scene, 1.0)
    a, b = _rect(True), _rect(True)
    layer.add(a)
    layer.add(b)
    assert layer.selected() is None
    b.setSelected(True)
    assert layer.selected() is b
