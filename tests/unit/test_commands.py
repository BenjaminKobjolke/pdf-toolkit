"""Unit tests for the command registry (offscreen Qt)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.gui import commands
from app.gui.main_window import MainWindow
from tests.conftest import MakePdf, gui_settings

_ALL_IDS = {
    commands.OPEN,
    commands.OPEN_HISTORY,
    commands.CLOSE_DOC,
    commands.EXIT,
    commands.PREV_PAGE,
    commands.NEXT_PAGE,
    commands.FIRST_PAGE,
    commands.LAST_PAGE,
    commands.ZOOM_FIT,
    commands.ZOOM_ACTUAL,
    commands.ZOOM_IN,
    commands.ZOOM_OUT,
    commands.SWAP,
    commands.DELETE_PAGE,
    commands.DELETE_RANGE,
    commands.INSERT_PAGE,
    commands.EXTRACT_PAGE,
    commands.MERGE_FOLDER,
    commands.ROTATE_LEFT,
    commands.ROTATE_RIGHT,
    commands.ROTATE_180,
    commands.MOVE_NEXT,
    commands.MOVE_PREV,
    commands.MOVE_FIRST,
    commands.MOVE_LAST,
    commands.SAVE,
    commands.PRINT,
    commands.SHOW_SHORTCUTS,
    commands.RELEASE_NOTES,
    commands.COMMAND_PALETTE,
    commands.CONFIGURE_SHORTCUTS,
    commands.RENAME_FILE,
    commands.TOGGLE_MENU,
    commands.TOGGLE_TOOLBAR,
    commands.TOGGLE_STATUSBAR,
    commands.TOGGLE_FULLSCREEN,
    commands.EDIT_MODE,
    commands.SELECT_NEXT,
    commands.SELECT_PREV,
    commands.ADD_FIELD,
    commands.ADD_IMAGE,
    commands.IMAGE_SCALE,
    commands.IMAGE_DELETE,
    commands.DELETE_FIELD,
    commands.EXPORT_TEXT,
    commands.DELETE_SAVED_FIELDS,
    commands.REMEMBERED_SETTINGS,
    commands.SEARCH_PDF,
    commands.SEARCH_FIELDS,
    commands.CLEAR_HIGHLIGHTS,
    commands.FIELD_CHANGE_TEXT,
    commands.FIELD_FONT_SIZE,
    commands.FIELD_FONT_FAMILY,
    commands.FIELD_TEXT_COLOR,
    commands.FIELD_BG_COLOR,
    commands.FIELD_TOGGLE_BOLD,
    commands.FIELD_TOGGLE_ITALIC,
    commands.FIELD_DELETE,
    commands.PALETTE_WIDTH,
    commands.PALETTE_HEIGHT,
    commands.PALETTE_FONT,
    commands.PALETTE_OPACITY,
    commands.PALETTE_BORDERLESS,
    commands.OUTLINE_WIDTH,
    commands.OUTLINE_STYLE,
    commands.OUTLINE_COLOR,
    commands.ZOOM_SET_DEFAULT,
    commands.DOC_ZOOM_REMEMBER,
    commands.DOC_PAGE_REMEMBER,
    commands.SET_DEFAULT_PDF_VIEWER,
    commands.REMOVE_PDF_HANDLER,
}


@pytest.fixture
def window(qapp: object, tmp_path: Path) -> MainWindow:
    return MainWindow(gui_settings(tmp_path))


def test_registry_covers_all_commands(window: MainWindow) -> None:
    registry = commands.build_commands(window)
    assert {c.command_id for c in registry} == _ALL_IDS


def test_titles_are_non_empty(window: MainWindow) -> None:
    for command in commands.build_commands(window):
        assert command.title


def test_find_returns_by_id(window: MainWindow) -> None:
    registry = commands.build_commands(window)
    assert commands.find(registry, commands.ZOOM_IN).command_id == commands.ZOOM_IN


def test_find_unknown_raises(window: MainWindow) -> None:
    with pytest.raises(KeyError):
        commands.find(commands.build_commands(window), "nope")


def test_doc_commands_disabled_without_document(window: MainWindow) -> None:
    registry = commands.build_commands(window)
    assert commands.find(registry, commands.ZOOM_IN).is_enabled() is False
    assert commands.find(registry, commands.NEXT_PAGE).is_enabled() is False
    assert commands.find(registry, commands.PRINT).is_enabled() is False
    # Always-available commands stay enabled.
    assert commands.find(registry, commands.OPEN).is_enabled() is True
    assert commands.find(registry, commands.EXIT).is_enabled() is True


def test_doc_commands_enabled_after_open(window: MainWindow, make_pdf: MakePdf) -> None:
    window.open_pdf(make_pdf([(200, 300), (200, 300)]))
    registry = commands.build_commands(window)
    assert commands.find(registry, commands.ZOOM_IN).is_enabled() is True
    assert commands.find(registry, commands.LAST_PAGE).is_enabled() is True


def test_field_commands_disabled_without_selection(window: MainWindow, make_pdf: MakePdf) -> None:
    window.open_pdf(make_pdf([(200, 300)]))
    registry = commands.build_commands(window)
    assert commands.find(registry, commands.FIELD_FONT_SIZE).is_enabled() is False
    assert commands.find(registry, commands.FIELD_DELETE).is_enabled() is False


def test_clear_highlights_enabled_only_with_highlights(
    window: MainWindow, make_pdf: MakePdf
) -> None:
    window.open_pdf(make_pdf([(200, 300)]))
    registry = commands.build_commands(window)
    assert commands.find(registry, commands.CLEAR_HIGHLIGHTS).is_enabled() is False
    window.page_view.set_highlights([(1.0, 2.0, 3.0, 4.0)])
    registry = commands.build_commands(window)
    assert commands.find(registry, commands.CLEAR_HIGHLIGHTS).is_enabled() is True
