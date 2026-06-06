"""Unit tests for Tab/Shift+Tab editable-element cycling (offscreen Qt)."""

from __future__ import annotations

from PySide6.QtGui import QPixmap

from app.gui.image_item import ImageItem
from app.gui.overlay_selection import select_adjacent_editable
from app.gui.page_view import PageView
from app.gui.text_item import TextFieldItem
from tests.conftest import MakeImage


def _populated_view(make_image: MakeImage) -> tuple[PageView, TextFieldItem, ImageItem]:
    view = PageView()
    text = TextFieldItem("hi")
    text.set_editable(True)
    text.setPos(10, 10)  # higher on the page -> first in reading order
    view.add_text_item(text)

    img = make_image("png")
    image = ImageItem(QPixmap(str(img)), "x.png", absolute=True)
    image.set_editable(True)
    image.setPos(10, 200)  # lower -> second
    view.add_image_item(image)
    return view, text, image


def test_cycles_in_reading_order(qapp: object, make_image: MakeImage) -> None:
    view, text, image = _populated_view(make_image)
    assert select_adjacent_editable(view, forward=True) is True
    assert text.isSelected()  # nothing selected -> first (top-most)
    select_adjacent_editable(view, forward=True)
    assert image.isSelected()
    select_adjacent_editable(view, forward=True)  # wraps
    assert text.isSelected()


def test_backward_wraps(qapp: object, make_image: MakeImage) -> None:
    view, text, image = _populated_view(make_image)
    select_adjacent_editable(view, forward=True)  # selects text
    select_adjacent_editable(view, forward=False)  # wraps back to image
    assert image.isSelected()


def test_noop_when_nothing_selectable(qapp: object, make_image: MakeImage) -> None:
    view, text, image = _populated_view(make_image)
    text.set_editable(False)
    image.set_editable(False)
    assert select_adjacent_editable(view, forward=True) is False
