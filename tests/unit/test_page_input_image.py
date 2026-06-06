"""Unit tests for image nudge/scale via page input (offscreen Qt)."""

from __future__ import annotations

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent, QPixmap

from app.gui.image_item import ImageItem
from app.gui.page_view import PageView
from tests.conftest import MakeImage


def _key(key: Qt.Key) -> QKeyEvent:
    return QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier)


def _selected_image(view: PageView, make_image: MakeImage) -> ImageItem:
    img = make_image("png", size=(20, 10))
    item = ImageItem(QPixmap(str(img)), "x.png", absolute=True)
    item.set_editable(True)
    view.add_image_item(item)
    item.setSelected(True)
    return item


def test_arrow_nudges_selected_image(qapp: object, make_image: MakeImage) -> None:
    view = PageView()
    item = _selected_image(view, make_image)
    view.keyPressEvent(_key(Qt.Key.Key_Right))
    assert item.pos().x() == 10.0


def test_plus_scales_selected_image(qapp: object, make_image: MakeImage) -> None:
    view = PageView()
    item = _selected_image(view, make_image)
    view.keyPressEvent(_key(Qt.Key.Key_Plus))
    assert round(item.scale_factor(), 3) == 1.1


def test_minus_shrinks_selected_image(qapp: object, make_image: MakeImage) -> None:
    view = PageView()
    item = _selected_image(view, make_image)
    view.keyPressEvent(_key(Qt.Key.Key_Minus))
    assert round(item.scale_factor(), 4) == round(1.0 / 1.1, 4)
