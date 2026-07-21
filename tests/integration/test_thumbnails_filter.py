"""Integration: the thumbnail filter-mode command and its footer label."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent

from app.gui import commands
from app.gui.main_window import MainWindow
from tests.conftest import MakeImage, MakePdf, silence_dialogs

# The ``window`` fixture comes from tests/conftest.py.


@pytest.fixture(autouse=True)
def _quiet_dialogs(monkeypatch: pytest.MonkeyPatch) -> None:
    silence_dialogs(monkeypatch)


def _start_filter(window: MainWindow) -> None:
    commands.find(window._registry, commands.FILTER_THUMBNAILS).run()


def _type(window: MainWindow, query: str) -> None:
    for char in query:
        window._thumbnails_view.keyPressEvent(
            QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier, char)
        )


def _visible(window: MainWindow) -> list[str]:
    grid = window._thumbnails_view
    return [grid.item(i).text() for i in range(grid.count()) if not grid.item(i).isHidden()]


def _press_escape(window: MainWindow) -> None:
    window._thumbnails_view.keyPressEvent(
        QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
    )


def test_filter_command_needs_a_document(window: MainWindow, make_pdf: MakePdf) -> None:
    command = commands.find(window._registry, commands.FILTER_THUMBNAILS)
    assert not command.is_enabled()
    window.open_pdf(make_pdf([(100, 100)], name="notes.pdf"))
    assert command.is_enabled()


def test_filter_command_enters_grid_and_shows_label(
    window: MainWindow, make_pdf: MakePdf, make_image: MakeImage
) -> None:
    doc = make_pdf([(100, 100)], name="notes.pdf")
    make_image(name="20260218_electronics.jpg")
    make_image(name="electronics.png")
    window.open_pdf(doc)
    assert not window._thumbnails.is_active()

    _start_filter(window)

    assert window._thumbnails.is_active()
    assert window._thumb_filter_label.isVisibleTo(window)
    assert window._thumb_filter_label.text() == "Filter: "

    _type(window, "elec jpg")
    assert _visible(window) == ["20260218_electronics.jpg"]
    assert "elec jpg" in window._thumb_filter_label.text()
    selected = window._thumbnails.selected_path()
    assert selected is not None and selected.name == "20260218_electronics.jpg"


def test_typing_without_filter_mode_does_not_filter(
    window: MainWindow, make_pdf: MakePdf, make_image: MakeImage
) -> None:
    doc = make_pdf([(100, 100)], name="notes.pdf")
    make_image(name="20260218_electronics.jpg")
    window.open_pdf(doc)
    commands.find(window._registry, commands.THUMBNAILS_VIEW).run()

    _type(window, "elec")
    assert len(_visible(window)) == 2
    assert not window._thumb_filter_label.isVisibleTo(window)


def test_escape_leaves_filter_mode_then_grid(
    window: MainWindow, make_pdf: MakePdf, make_image: MakeImage
) -> None:
    doc = make_pdf([(100, 100)], name="notes.pdf")
    make_image(name="20260218_electronics.jpg")
    window.open_pdf(doc)
    _start_filter(window)
    _type(window, "elec")

    _press_escape(window)
    assert not window._thumb_filter_label.isVisibleTo(window)
    assert len(_visible(window)) == 2
    assert window._thumbnails.is_active()

    _press_escape(window)
    assert not window._thumbnails.is_active()


def test_reentering_grid_resets_filter_mode(
    window: MainWindow, make_pdf: MakePdf, make_image: MakeImage
) -> None:
    doc = make_pdf([(100, 100)], name="notes.pdf")
    make_image(name="20260218_electronics.jpg")
    window.open_pdf(doc)
    _start_filter(window)
    _type(window, "elec")
    window._thumbnails.leave()

    commands.find(window._registry, commands.THUMBNAILS_VIEW).run()
    assert len(_visible(window)) == 2
    assert not window._thumb_filter_label.isVisibleTo(window)
