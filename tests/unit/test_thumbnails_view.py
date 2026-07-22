"""Unit tests for the thumbnails grid widget, mainly the explicit filter mode.

The view is constructed directly (offscreen ``qapp``) and populated with
nonexistent paths: without a running event loop the zero-interval render timer
never fires, so no real files are needed.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent

from app.gui.thumbnails_view import ThumbnailsView

pytestmark = pytest.mark.usefixtures("qapp")

FILES = ["20260218_electronics.jpg", "electronics.png", "notes.pdf"]


@pytest.fixture
def view() -> ThumbnailsView:
    grid = ThumbnailsView()
    grid.populate([Path(name) for name in FILES], Path("notes.pdf"))
    return grid


@pytest.fixture
def filtering(view: ThumbnailsView) -> ThumbnailsView:
    view.start_filter()
    return view


def _key(
    view: ThumbnailsView,
    key: Qt.Key,
    text: str = "",
    mods: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
) -> None:
    view.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, key, mods, text))


def _type(view: ThumbnailsView, query: str) -> None:
    for char in query:
        _key(view, Qt.Key.Key_A, char)


def _visible(view: ThumbnailsView) -> list[str]:
    return [view.item(i).text() for i in range(view.count()) if not view.item(i).isHidden()]


def _shortcut_override(view: ThumbnailsView, char: str) -> bool:
    event = QKeyEvent(
        QEvent.Type.ShortcutOverride, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier, char
    )
    event.ignore()
    view.event(event)
    return event.isAccepted()


def test_typing_without_filter_mode_does_not_filter(view: ThumbnailsView) -> None:
    _type(view, "elec")
    assert _visible(view) == FILES


def test_typing_in_filter_mode_hides_non_matching_items(filtering: ThumbnailsView) -> None:
    _type(filtering, "elec")
    assert _visible(filtering) == ["20260218_electronics.jpg", "electronics.png"]


def test_start_filter_emits_mode_and_text(view: ThumbnailsView) -> None:
    modes: list[bool] = []
    texts: list[str] = []
    view.filter_mode_changed.connect(modes.append)
    view.filter_changed.connect(texts.append)
    view.start_filter()
    assert modes == [True]
    assert texts == [""]


def test_typing_emits_filter_changed(filtering: ThumbnailsView) -> None:
    seen: list[str] = []
    filtering.filter_changed.connect(seen.append)
    _type(filtering, "el")
    assert seen == ["e", "el"]


def test_second_term_narrows_with_and_semantics(filtering: ThumbnailsView) -> None:
    _type(filtering, "elec jpg")
    assert _visible(filtering) == ["20260218_electronics.jpg"]


def test_backspace_widens(filtering: ThumbnailsView) -> None:
    _type(filtering, "elec j")
    _key(filtering, Qt.Key.Key_Backspace)
    _key(filtering, Qt.Key.Key_Backspace)
    assert _visible(filtering) == ["20260218_electronics.jpg", "electronics.png"]


def test_selection_moves_to_first_visible_when_current_hidden(
    filtering: ThumbnailsView,
) -> None:
    assert filtering.selected_path() == Path("notes.pdf")
    _type(filtering, "elec")
    assert filtering.selected_path() == Path("20260218_electronics.jpg")


def test_selection_preserved_when_still_visible(filtering: ThumbnailsView) -> None:
    filtering.setCurrentRow(1)  # electronics.png
    _type(filtering, "elec")
    assert filtering.selected_path() == Path("electronics.png")


def test_zero_matches_clears_selection(filtering: ThumbnailsView) -> None:
    _type(filtering, "zzz")
    assert _visible(filtering) == []
    assert filtering.selected_path() is None


def test_escape_exits_filter_mode_without_dismissing(filtering: ThumbnailsView) -> None:
    dismissed: list[bool] = []
    modes: list[bool] = []
    filtering.dismiss_requested.connect(lambda: dismissed.append(True))
    filtering.filter_mode_changed.connect(modes.append)
    _type(filtering, "elec")
    _key(filtering, Qt.Key.Key_Escape)
    assert _visible(filtering) == FILES
    assert dismissed == []
    assert modes == [False]


def test_escape_outside_filter_mode_dismisses(view: ThumbnailsView) -> None:
    dismissed: list[bool] = []
    view.dismiss_requested.connect(lambda: dismissed.append(True))
    _key(view, Qt.Key.Key_Escape)
    assert dismissed == [True]


def test_escape_after_leaving_filter_mode_dismisses(filtering: ThumbnailsView) -> None:
    dismissed: list[bool] = []
    filtering.dismiss_requested.connect(lambda: dismissed.append(True))
    _key(filtering, Qt.Key.Key_Escape)
    assert dismissed == []
    _key(filtering, Qt.Key.Key_Escape)
    assert dismissed == [True]


def test_populate_keeps_filter_while_mode_active(filtering: ThumbnailsView) -> None:
    _type(filtering, "elec jpg")
    filtering.populate([Path(name) for name in FILES], Path("notes.pdf"))
    assert _visible(filtering) == ["20260218_electronics.jpg"]


def test_clear_filter_exits_mode_and_shows_all(filtering: ThumbnailsView) -> None:
    texts: list[str] = []
    modes: list[bool] = []
    _type(filtering, "elec")
    filtering.filter_changed.connect(texts.append)
    filtering.filter_mode_changed.connect(modes.append)
    filtering.clear_filter()
    assert texts == [""]
    assert modes == [False]
    assert _visible(filtering) == FILES


def test_clear_filter_is_noop_when_inactive(view: ThumbnailsView) -> None:
    modes: list[bool] = []
    view.filter_mode_changed.connect(modes.append)
    view.clear_filter()
    assert modes == []


def test_ctrl_chords_do_not_touch_filter(filtering: ThumbnailsView) -> None:
    _key(filtering, Qt.Key.Key_A, "a", Qt.KeyboardModifier.ControlModifier)
    assert _visible(filtering) == FILES


def test_shortcut_override_accepted_in_filter_mode(filtering: ThumbnailsView) -> None:
    assert _shortcut_override(filtering, "a")


def test_shortcut_override_ignored_outside_filter_mode(view: ThumbnailsView) -> None:
    assert not _shortcut_override(view, "a")


def _nav_override(
    view: ThumbnailsView,
    key: Qt.Key,
    mods: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
) -> bool:
    event = QKeyEvent(QEvent.Type.ShortcutOverride, key, mods)
    event.ignore()
    view.event(event)
    return event.isAccepted()


def test_navigation_keys_claimed_from_shortcuts_outside_filter_mode(
    view: ThumbnailsView,
) -> None:
    # A user-bound single-key shortcut (e.g. Right -> next file) must not steal
    # grid navigation.
    for key in (
        Qt.Key.Key_Left,
        Qt.Key.Key_Right,
        Qt.Key.Key_Up,
        Qt.Key.Key_Down,
        Qt.Key.Key_Home,
        Qt.Key.Key_End,
        Qt.Key.Key_PageUp,
        Qt.Key.Key_PageDown,
        Qt.Key.Key_Return,
        Qt.Key.Key_Enter,
        Qt.Key.Key_Escape,
    ):
        assert _nav_override(view, key), key


def test_modified_navigation_keys_stay_with_shortcuts(view: ThumbnailsView) -> None:
    # Ctrl+Up/Down = thumbnail zoom, Alt+Right/Left = next/prev file.
    assert not _nav_override(view, Qt.Key.Key_Up, Qt.KeyboardModifier.ControlModifier)
    assert not _nav_override(view, Qt.Key.Key_Down, Qt.KeyboardModifier.ControlModifier)
    assert not _nav_override(view, Qt.Key.Key_Right, Qt.KeyboardModifier.AltModifier)
    assert not _nav_override(view, Qt.Key.Key_Left, Qt.KeyboardModifier.AltModifier)


def test_enter_in_filter_mode_opens_selected_file(filtering: ThumbnailsView) -> None:
    opened: list[Path] = []
    filtering.open_requested.connect(opened.append)
    _type(filtering, "elec jpg")
    _key(filtering, Qt.Key.Key_Return)
    assert opened == [Path("20260218_electronics.jpg")]
