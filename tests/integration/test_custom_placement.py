"""Integration tests for centered and custom text-field placement."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QKeyEvent

from app.gui.crosshair_item import CrosshairItem
from app.gui.main_window import MainWindow
from app.gui.page_view import PageView
from tests.conftest import MakePdf


def _press(view: PageView, key: Qt.Key, shift: bool = False) -> None:
    mods = Qt.KeyboardModifier.ShiftModifier if shift else Qt.KeyboardModifier.NoModifier
    view.keyPressEvent(QKeyEvent(QKeyEvent.Type.KeyPress, key, mods))


def _crosshairs(view: PageView) -> list[CrosshairItem]:
    return [item for item in view.graphics_scene().items() if isinstance(item, CrosshairItem)]


def _begin_custom(window: MainWindow) -> list[QPointF | None]:
    done: list[QPointF | None] = []

    def on_done(point: QPointF | None) -> None:
        done.append(point)
        if point is not None:
            window._controller.add_field(point, centered=True)

    window._page_view.begin_custom_placement(on_done)
    return done


def test_add_field_page_center_centers_field(window: MainWindow, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400)])
    window.open_pdf(pdf)
    window._controller.set_edit_mode(True)
    center = window._page_view.page_center()

    window._controller.add_field(center, centered=True)

    item = window._page_view.text_items()[0]
    offset = item.boundingRect().center()
    assert item.pos().x() == pytest.approx(center.x() - offset.x())
    assert item.pos().y() == pytest.approx(center.y() - offset.y())


def test_add_field_view_center_lands_on_page(window: MainWindow, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400)])
    window.open_pdf(pdf)
    window._controller.set_edit_mode(True)

    window._controller.add_field(window._page_view.viewport_center_scene(), centered=True)

    item = window._page_view.text_items()[0]
    assert window._page_view.graphics_scene().sceneRect().contains(item.pos())


def test_custom_placement_enter_creates_field_at_crosshair(
    window: MainWindow, make_pdf: MakePdf
) -> None:
    pdf = make_pdf([(300, 400)])
    window.open_pdf(pdf)
    window._controller.set_edit_mode(True)

    _begin_custom(window)
    assert len(_crosshairs(window._page_view)) == 1
    crosshair_pos = _crosshairs(window._page_view)[0].pos()
    _press(window._page_view, Qt.Key.Key_Return)

    item = window._page_view.text_items()[0]
    offset = item.boundingRect().center()
    assert item.pos().x() == pytest.approx(crosshair_pos.x() - offset.x())
    assert _crosshairs(window._page_view) == []


def test_custom_placement_arrow_moves_crosshair(window: MainWindow, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400)])
    window.open_pdf(pdf)
    window._controller.set_edit_mode(True)

    _begin_custom(window)
    start = _crosshairs(window._page_view)[0].pos()
    _press(window._page_view, Qt.Key.Key_Right)
    assert _crosshairs(window._page_view)[0].pos().x() == pytest.approx(start.x() + 10.0)

    _press(window._page_view, Qt.Key.Key_Down, shift=True)
    assert _crosshairs(window._page_view)[0].pos().y() == pytest.approx(start.y() + 1.0)


def test_custom_placement_escape_cancels(window: MainWindow, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400)])
    window.open_pdf(pdf)
    window._controller.set_edit_mode(True)

    done = _begin_custom(window)
    _press(window._page_view, Qt.Key.Key_Escape)

    assert done == [None]
    assert window._page_view.text_items() == ()
    assert _crosshairs(window._page_view) == []


def test_custom_placement_click_creates_field(window: MainWindow, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400)])
    window.open_pdf(pdf)
    window._controller.set_edit_mode(True)

    _begin_custom(window)
    window._page_view._input.mouse_press(QPointF(120.0, 150.0))

    assert len(window._page_view.text_items()) == 1
    assert _crosshairs(window._page_view) == []
