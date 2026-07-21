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
    assert bar.mode_text() == strings.MODE_EDIT


def test_toggling_back_returns_to_regular(bar: ModeStatusBar) -> None:
    bar.set_edit_mode(True)
    bar.set_edit_mode(False)
    assert bar.mode_text() == strings.MODE_REGULAR


def test_page_label_blank_by_default(bar: ModeStatusBar) -> None:
    assert bar.page_text() == ""


def test_set_page_label_shows_current_of_total(bar: ModeStatusBar) -> None:
    bar.set_page_label(5, 7)
    assert bar.page_text() == "Page 5/7"


def test_clear_page_label_blanks_it(bar: ModeStatusBar) -> None:
    bar.set_page_label(5, 7)
    bar.clear_page_label()
    assert bar.page_text() == ""


def test_file_label_blank_and_hidden_by_default(bar: ModeStatusBar) -> None:
    assert bar.file_text() == ""
    assert bar._file_label.isHidden()


def test_set_file_label_shows_position(bar: ModeStatusBar) -> None:
    bar.set_file_label(2, 5)
    assert bar.file_text() == "File 2/5"
    assert not bar._file_label.isHidden()


def test_clear_file_label_blanks_and_hides(bar: ModeStatusBar) -> None:
    bar.set_file_label(2, 5)
    bar.clear_file_label()
    assert bar.file_text() == ""
    assert bar._file_label.isHidden()


def test_clear_page_label_keeps_file_label(bar: ModeStatusBar) -> None:
    bar.set_file_label(2, 5)
    bar.set_page_label(3, 10)
    bar.clear_page_label()
    assert bar.file_text() == "File 2/5"
    assert bar._page_label.isHidden()


def test_unpaged_document_shows_bare_file_counter(bar: ModeStatusBar) -> None:
    bar.set_paged_document(False)
    bar.set_file_label(6, 7)
    assert bar.file_text() == "6/7"


def test_unpaged_document_ignores_page_label(bar: ModeStatusBar) -> None:
    bar.set_paged_document(False)
    bar.set_page_label(1, 1)
    assert bar.page_text() == ""
    assert bar._page_label.isHidden()


def test_switching_to_unpaged_clears_stale_page_label(bar: ModeStatusBar) -> None:
    bar.set_page_label(3, 10)
    bar.set_paged_document(False)
    assert bar.page_text() == ""
    assert bar._page_label.isHidden()


def test_switching_back_to_paged_restores_labeled_rows(bar: ModeStatusBar) -> None:
    bar.set_paged_document(False)
    bar.set_paged_document(True)
    bar.set_file_label(2, 5)
    bar.set_page_label(3, 10)
    assert bar.file_text() == "File 2/5"
    assert bar.page_text() == "Page 3/10"


def test_zoom_label_blank_by_default(bar: ModeStatusBar) -> None:
    assert bar.zoom_text() == ""


def test_set_zoom_label_shows_percent(bar: ModeStatusBar) -> None:
    bar.set_zoom_label(150)
    assert bar.zoom_text() == "150%"


def test_clear_zoom_label_blanks_it(bar: ModeStatusBar) -> None:
    bar.set_zoom_label(150)
    bar.clear_zoom_label()
    assert bar.zoom_text() == ""


def test_flash_shows_centered_message_and_timer_clears_it(bar: ModeStatusBar) -> None:
    bar.flash("copied file path")
    assert bar.flash_text() == "copied file path"
    assert bar.mode_text() == strings.MODE_REGULAR  # mode label untouched
    bar._flash_timer.timeout.emit()  # fire the auto-hide without an event loop
    assert bar.flash_text() == ""


def test_flash_blank_by_default(bar: ModeStatusBar) -> None:
    assert bar.flash_text() == ""


def test_second_flash_replaces_first(bar: ModeStatusBar) -> None:
    bar.flash("first")
    bar.flash("second")
    assert bar.flash_text() == "second"
    bar._flash_timer.timeout.emit()
    assert bar.flash_text() == ""


def test_mode_change_leaves_flash_running(bar: ModeStatusBar) -> None:
    bar.flash("copied")
    bar.set_edit_mode(True)
    assert bar.mode_text() == strings.MODE_EDIT
    assert bar.flash_text() == "copied"
    assert bar._flash_timer.isActive() is True


def test_dirty_marker_blank_by_default(bar: ModeStatusBar) -> None:
    assert bar.dirty_text() == ""


def test_set_dirty_shows_marker(bar: ModeStatusBar) -> None:
    bar.set_dirty(True)
    assert bar.dirty_text() == strings.MODIFIED_MARKER


def test_clear_dirty_blanks_marker(bar: ModeStatusBar) -> None:
    bar.set_dirty(True)
    bar.set_dirty(False)
    assert bar.dirty_text() == ""
