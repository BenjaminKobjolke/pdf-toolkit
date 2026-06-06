"""Unit tests for the mode footer bar (offscreen Qt)."""

from __future__ import annotations

import pytest

from app.gui import strings
from app.gui.mode_status_bar import ModeStatusBar


@pytest.fixture
def bar(qapp: object) -> ModeStatusBar:
    return ModeStatusBar()


def test_defaults_to_regular_mode(bar: ModeStatusBar) -> None:
    assert bar.mode_text() == strings.MODE_REGULAR


def test_edit_mode_shows_edit_text(bar: ModeStatusBar) -> None:
    bar.set_edit_mode(True)
    assert bar.mode_text() == strings.MODE_EDIT_TEXT


def test_toggling_back_returns_to_regular(bar: ModeStatusBar) -> None:
    bar.set_edit_mode(True)
    bar.set_edit_mode(False)
    assert bar.mode_text() == strings.MODE_REGULAR


def test_page_label_blank_by_default(bar: ModeStatusBar) -> None:
    assert bar.page_text() == ""


def test_set_page_label_shows_current_of_total(bar: ModeStatusBar) -> None:
    bar.set_page_label(5, 7)
    assert bar.page_text() == "5/7"


def test_clear_page_label_blanks_it(bar: ModeStatusBar) -> None:
    bar.set_page_label(5, 7)
    bar.clear_page_label()
    assert bar.page_text() == ""


def test_dirty_marker_blank_by_default(bar: ModeStatusBar) -> None:
    assert bar.dirty_text() == ""


def test_set_dirty_shows_marker(bar: ModeStatusBar) -> None:
    bar.set_dirty(True)
    assert bar.dirty_text() == strings.MODIFIED_MARKER


def test_clear_dirty_blanks_marker(bar: ModeStatusBar) -> None:
    bar.set_dirty(True)
    bar.set_dirty(False)
    assert bar.dirty_text() == ""
