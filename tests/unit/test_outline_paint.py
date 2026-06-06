"""Selected items draw the custom outline; unselected ones don't."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QStyle, QStyleOptionGraphicsItem

from app.gui import outline_style
from app.gui.image_item import ImageItem
from app.gui.outline_style import OutlineStyle
from app.gui.text_item import TextFieldItem


@pytest.fixture
def spy_holder(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Replace the active outline holder with a spy for the duration of a test."""
    holder = MagicMock(spec=OutlineStyle)
    monkeypatch.setattr(outline_style, "active", lambda: holder)
    return holder


def _option(*, selected: bool) -> QStyleOptionGraphicsItem:
    option = QStyleOptionGraphicsItem()
    if selected:
        option.state |= QStyle.StateFlag.State_Selected
    return option


def test_selected_text_item_draws_outline(qapp: object, spy_holder: MagicMock) -> None:
    item = TextFieldItem("hi")
    pixmap = QPixmap(64, 64)
    painter = QPainter(pixmap)
    try:
        item.paint(painter, _option(selected=True))
    finally:
        painter.end()
    spy_holder.draw.assert_called_once()


def test_unselected_text_item_skips_outline(qapp: object, spy_holder: MagicMock) -> None:
    item = TextFieldItem("hi")
    pixmap = QPixmap(64, 64)
    painter = QPainter(pixmap)
    try:
        item.paint(painter, _option(selected=False))
    finally:
        painter.end()
    spy_holder.draw.assert_not_called()


def test_selected_image_item_draws_outline(
    qapp: object, spy_holder: MagicMock, make_image: object
) -> None:
    img: Path = make_image()  # type: ignore[operator]
    item = ImageItem(QPixmap(str(img)), "x.png", absolute=True)
    pixmap = QPixmap(64, 64)
    painter = QPainter(pixmap)
    try:
        item.paint(painter, _option(selected=True))
    finally:
        painter.end()
    spy_holder.draw.assert_called_once()


def test_unselected_image_item_skips_outline(
    qapp: object, spy_holder: MagicMock, make_image: object
) -> None:
    img: Path = make_image()  # type: ignore[operator]
    item = ImageItem(QPixmap(str(img)), "x.png", absolute=True)
    pixmap = QPixmap(64, 64)
    painter = QPainter(pixmap)
    try:
        item.paint(painter, _option(selected=False))
    finally:
        painter.end()
    spy_holder.draw.assert_not_called()
