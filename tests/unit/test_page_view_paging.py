"""Arrow-key page flipping at scroll edges (offscreen Qt)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QKeyEvent, QWheelEvent

from app.gui.page_view import PageView
from app.gui.text_item import TextFieldItem
from tests.conftest import MakePdf


@pytest.fixture
def view(qapp: object, make_pdf: MakePdf) -> PageView:
    page_view = PageView()
    page_view.load(make_pdf([(200, 300), (200, 300), (200, 300)]))
    return page_view


def _press(view: PageView, key: Qt.Key) -> None:
    view.keyPressEvent(QKeyEvent(QKeyEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier))


def _wheel(
    view: PageView,
    dy: int,
    mods: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
) -> None:
    event = QWheelEvent(
        QPointF(0, 0),
        QPointF(0, 0),
        QPoint(0, 0),
        QPoint(0, dy),
        Qt.MouseButton.NoButton,
        mods,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    view.wheelEvent(event)


def test_down_at_bottom_goes_next(view: PageView) -> None:
    _press(view, Qt.Key.Key_Down)
    assert view.current_page_one_based() == 2


def test_up_at_top_goes_prev(view: PageView) -> None:
    view.go_to_page(2)
    _press(view, Qt.Key.Key_Up)
    assert view.current_page_one_based() == 2


def test_down_stops_at_last_page(view: PageView) -> None:
    view.go_to_page(2)
    _press(view, Qt.Key.Key_Down)
    assert view.current_page_one_based() == 3


def test_up_stops_at_first_page(view: PageView) -> None:
    _press(view, Qt.Key.Key_Up)
    assert view.current_page_one_based() == 1


def test_wheel_down_at_bottom_goes_next(view: PageView) -> None:
    _wheel(view, -120)
    assert view.current_page_one_based() == 2


def test_wheel_up_at_top_goes_prev(view: PageView) -> None:
    view.go_to_page(2)
    _wheel(view, 120)
    assert view.current_page_one_based() == 2


def test_wheel_down_stops_at_last_page(view: PageView) -> None:
    view.go_to_page(2)
    _wheel(view, -120)
    assert view.current_page_one_based() == 3


def test_ctrl_wheel_down_goes_next(view: PageView) -> None:
    _wheel(view, -120, Qt.KeyboardModifier.ControlModifier)
    assert view.current_page_one_based() == 2


def test_ctrl_wheel_up_stops_at_first_page(view: PageView) -> None:
    _wheel(view, 120, Qt.KeyboardModifier.ControlModifier)
    assert view.current_page_one_based() == 1


def test_shift_wheel_does_not_flip_page(view: PageView) -> None:
    _wheel(view, -120, Qt.KeyboardModifier.ShiftModifier)
    assert view.current_page_one_based() == 1


def test_arrows_nudge_selected_field_instead_of_flipping(view: PageView) -> None:
    item = TextFieldItem("x")
    item.set_editable(True)
    view.add_text_item(item)
    item.setSelected(True)
    before = item.pos().y()
    _press(view, Qt.Key.Key_Down)
    # A selected field consumes the arrow as a nudge; the page does not flip.
    assert view.current_page_one_based() == 1
    assert item.pos().y() > before
