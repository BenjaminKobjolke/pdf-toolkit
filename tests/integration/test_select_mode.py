"""Integration tests for vim-style text select / copy mode (offscreen Qt)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication

from app.gui import commands, render, select_strings
from app.gui.main_window import MainWindow
from app.pdf.words import WordBox, page_words
from tests.conftest import MakeSearchablePdf, gui_settings, silence_dialogs


def _word(pdf: object, text: str) -> WordBox:
    return next(w for w in page_words(pdf, 0) if w.text == text)  # type: ignore[arg-type]


def _scene_center(word: WordBox) -> QPointF:
    z = render.DEFAULT_ZOOM
    return QPointF((word.x0 + word.x1) / 2 * z, (word.y0 + word.y1) / 2 * z)


@pytest.fixture
def window(qapp: object, tmp_path: Path) -> MainWindow:
    return MainWindow(gui_settings(tmp_path))


def _press(window: MainWindow, text: str, key: Qt.Key = Qt.Key.Key_unknown) -> None:
    event = QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier, text)
    window.select_controller.handle_key(event)


def test_select_mode_toggles_and_shows_hint(
    window: MainWindow, make_searchable_pdf: MakeSearchablePdf
) -> None:
    window.open_pdf(make_searchable_pdf(["hello world"]))
    commands.find(commands.build_commands(window), commands.SELECT_MODE).run()
    assert window.select_controller.is_active()
    assert window.mode_bar.mode_text() == select_strings.MODE_SELECT


def test_visual_select_and_yank_copies_span(
    window: MainWindow, make_searchable_pdf: MakeSearchablePdf
) -> None:
    window.open_pdf(make_searchable_pdf(["the quick brown fox"]))
    window.toggle_select_mode()

    _press(window, "v")  # start visual selection on "the"
    assert window.mode_bar.mode_text() == select_strings.MODE_SELECT_VISUAL
    _press(window, "l")  # extend to "quick"
    _press(window, "l")  # extend to "brown"
    _press(window, "y")  # yank

    assert QApplication.clipboard().text() == "the quick brown"
    # After yank the visual selection is dropped but the mode stays active.
    assert window.select_controller.is_active()
    assert window.mode_bar.mode_text() == select_strings.MODE_SELECT


def test_arrow_keys_move_like_hjkl(
    window: MainWindow, make_searchable_pdf: MakeSearchablePdf
) -> None:
    window.open_pdf(make_searchable_pdf(["the quick brown fox"]))
    window.toggle_select_mode()  # cursor on "the"

    _press(window, "", Qt.Key.Key_Right)  # -> quick
    _press(window, "", Qt.Key.Key_Right)  # -> brown
    _press(window, "", Qt.Key.Key_Left)  # -> quick
    _press(window, "y")

    assert QApplication.clipboard().text() == "quick"


def test_entering_edit_mode_exits_select_mode(
    window: MainWindow, make_searchable_pdf: MakeSearchablePdf
) -> None:
    window.open_pdf(make_searchable_pdf(["alpha beta"]))
    window.toggle_select_mode()
    assert window.select_controller.is_active()

    window.toggle_edit_mode()  # mutually exclusive
    assert not window.select_controller.is_active()


def test_entering_select_mode_exits_edit_mode(
    window: MainWindow, make_searchable_pdf: MakeSearchablePdf
) -> None:
    window.open_pdf(make_searchable_pdf(["alpha beta"]))
    window.toggle_edit_mode()
    assert window.edit_bar.is_edit_mode()

    window.toggle_select_mode()
    assert window.select_controller.is_active()
    assert not window.edit_bar.is_edit_mode()


def test_escape_exits_select_mode(
    window: MainWindow, make_searchable_pdf: MakeSearchablePdf
) -> None:
    window.open_pdf(make_searchable_pdf(["alpha beta"]))
    window.toggle_select_mode()
    _press(window, "\x1b", Qt.Key.Key_Escape)
    assert not window.select_controller.is_active()


def test_select_mode_seeds_cursor_from_search_highlight(
    window: MainWindow, make_searchable_pdf: MakeSearchablePdf
) -> None:
    pdf = make_searchable_pdf(["alpha beta gamma"])
    window.open_pdf(pdf)
    beta = _word(pdf, "beta")
    window.page_view.set_highlights([(beta.x0, beta.y0, beta.x1, beta.y1)])

    window.toggle_select_mode()  # seeds on the highlighted word
    _press(window, "y")  # no visual selection -> copies the word under the cursor

    assert QApplication.clipboard().text() == "beta"
    assert not window.page_view.has_highlights()  # gold seed consumed


def test_click_places_cursor(window: MainWindow, make_searchable_pdf: MakeSearchablePdf) -> None:
    pdf = make_searchable_pdf(["alpha beta gamma"])
    window.open_pdf(pdf)
    window.toggle_select_mode()  # starts on "alpha"

    window.select_controller.handle_click(_scene_center(_word(pdf, "gamma")))
    _press(window, "y")

    assert QApplication.clipboard().text() == "gamma"


def test_escape_clears_search_highlight_when_not_selecting(
    window: MainWindow, make_searchable_pdf: MakeSearchablePdf
) -> None:
    window.open_pdf(make_searchable_pdf(["alpha beta"]))
    window.page_view.set_highlights([(1.0, 2.0, 3.0, 4.0)])

    event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
    window.page_view.keyPressEvent(event)

    assert not window.page_view.has_highlights()


def test_copy_page_text_command(
    window: MainWindow, make_searchable_pdf: MakeSearchablePdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    silence_dialogs(monkeypatch)
    window.open_pdf(make_searchable_pdf(["hello world", "second page"]))
    commands.find(commands.build_commands(window), commands.COPY_PAGE_TEXT).run()
    assert QApplication.clipboard().text().strip() == "hello world"
