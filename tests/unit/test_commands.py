"""Unit tests for the command registry (offscreen Qt)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.gui import commands, overlay_commands
from app.gui.commands import Command
from app.gui.main_window import MainWindow
from tests.conftest import MakePdf, gui_settings

_ALL_IDS = {
    commands.OPEN,
    commands.OPEN_DIR,
    commands.OPEN_HISTORY,
    commands.OPEN_FOLDER_HISTORY,
    commands.NEXT_FILE,
    commands.PREV_FILE,
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
    commands.FLIP_HORIZONTAL,
    commands.FLIP_VERTICAL,
    commands.MOVE_NEXT,
    commands.MOVE_PREV,
    commands.MOVE_FIRST,
    commands.MOVE_LAST,
    commands.SAVE,
    commands.SAVE_AS,
    commands.COPY_FILE_PATH,
    commands.COPY_FILE_NAME,
    commands.COPY_FILE_NAME_NO_EXT,
    commands.COPY_PAGE_TEXT,
    # Pinned literally: generated from COPY_IMAGE_PERCENTS, ids must never drift.
    "copy_page_image",
    "copy_page_image_50",
    "copy_page_image_25",
    commands.COPY_VIEW_IMAGE,
    "copy_view_image_50",
    "copy_view_image_25",
    commands.OPEN_FOLDER,
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
    commands.SELECT_MODE,
    commands.OPEN_LINK,
    commands.COPY_LINK,
    commands.LINK_FONT,
    commands.LINK_TEXT_COLOR,
    commands.LINK_BG_COLOR,
    commands.LINK_BOX_COLOR,
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
    commands.DIALOG_SIZE,
    commands.PALETTE_WIDTH,
    commands.PALETTE_HEIGHT,
    commands.PALETTE_FONT,
    commands.PALETTE_OPACITY,
    commands.PALETTE_BORDERLESS,
    commands.OUTLINE_WIDTH,
    commands.OUTLINE_STYLE,
    commands.OUTLINE_COLOR,
    commands.TEXT_DARK_MODE,
    commands.TEXT_FONT_SIZE,
    commands.OPEN_FILTER_ALL_FILES,
    commands.OPEN_FILTER_EXTENSIONS,
    commands.REUSE_WINDOW,
    commands.FOCUS_ON_FORWARD,
    commands.RELOAD_DOC,
    commands.RELOAD_WATCH_SESSION,
    commands.RELOAD_WATCH_DEFAULT,
    commands.ZOOM_SET_DEFAULT,
    commands.DOC_ZOOM_REMEMBER,
    commands.DOC_PAGE_REMEMBER,
    commands.FILE_TYPE_ASSOCIATIONS,
    overlay_commands.ADD_RECT,
    overlay_commands.RECT_FILL_COLOR,
    overlay_commands.RECT_WIDTH,
    overlay_commands.RECT_HEIGHT,
    overlay_commands.RECT_DELETE,
    overlay_commands.LAYER_FORWARD,
    overlay_commands.LAYER_BACKWARD,
    overlay_commands.LAYER_TO_FRONT,
    overlay_commands.LAYER_TO_BACK,
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


def test_history_command_titles(window: MainWindow) -> None:
    registry = commands.build_commands(window)
    assert commands.find(registry, commands.OPEN).title == "Open file…"
    assert (
        commands.find(registry, commands.OPEN_HISTORY).title == "Open file from recent / history…"
    )
    assert (
        commands.find(registry, commands.OPEN_FOLDER_HISTORY).title
        == "Open folder from recent / history…"
    )


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
    assert commands.find(registry, commands.SAVE_AS).is_enabled() is False
    assert commands.find(registry, commands.COPY_FILE_PATH).is_enabled() is False
    assert commands.find(registry, commands.OPEN_FOLDER).is_enabled() is False
    assert commands.find(registry, "copy_page_image").is_enabled() is False
    assert commands.find(registry, commands.COPY_VIEW_IMAGE).is_enabled() is False
    # Always-available commands stay enabled.
    assert commands.find(registry, commands.OPEN).is_enabled() is True
    assert commands.find(registry, commands.EXIT).is_enabled() is True


def test_doc_commands_enabled_after_open(window: MainWindow, make_pdf: MakePdf) -> None:
    window.open_pdf(make_pdf([(200, 300), (200, 300)]))
    registry = commands.build_commands(window)
    assert commands.find(registry, commands.ZOOM_IN).is_enabled() is True
    assert commands.find(registry, commands.LAST_PAGE).is_enabled() is True


def test_next_file_opens_alphabetical_sibling(window: MainWindow, make_pdf: MakePdf) -> None:
    first = make_pdf([(200, 300)], name="a.pdf")
    second = make_pdf([(200, 300)], name="b.pdf")
    window.open_pdf(first)
    commands.find(commands.build_commands(window), commands.NEXT_FILE).run()
    assert window._source == second


def test_prev_file_wraps_to_last_sibling(window: MainWindow, make_pdf: MakePdf) -> None:
    first = make_pdf([(200, 300)], name="a.pdf")
    last = make_pdf([(200, 300)], name="z.pdf")
    window.open_pdf(first)
    commands.find(commands.build_commands(window), commands.PREV_FILE).run()
    assert window._source == last


def test_next_file_solo_document_stays_open(window: MainWindow, make_pdf: MakePdf) -> None:
    only = make_pdf([(200, 300)], name="only.pdf")
    window.open_pdf(only)
    commands.find(commands.build_commands(window), commands.NEXT_FILE).run()
    assert window._source == only


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


# --- dynamic pixel-size titles -------------------------------------------------


def test_copy_image_titles_fall_back_to_static_without_document(window: MainWindow) -> None:
    registry = commands.build_commands(window)
    assert commands.find(registry, "copy_page_image").display_title() == "Copy page as image"
    assert commands.find(registry, "copy_page_image_50").display_title() == (
        "Copy page as image at 50%"
    )
    assert commands.find(registry, commands.COPY_VIEW_IMAGE).display_title() == (
        "Copy current view to clipboard"
    )
    assert commands.find(registry, "copy_view_image_50").display_title() == (
        "Copy current view at 50%"
    )


def test_page_image_titles_show_pixels_with_document(window: MainWindow, make_pdf: MakePdf) -> None:
    window.open_pdf(make_pdf([(200, 100)]))
    registry = commands.build_commands(window)
    assert commands.find(registry, "copy_page_image").display_title() == (
        "Copy page as image (200×100 px)"
    )
    assert commands.find(registry, "copy_page_image_50").display_title() == (
        "Copy page as image at 50% (100×50 px)"
    )
    assert commands.find(registry, "copy_page_image_25").display_title() == (
        "Copy page as image at 25% (50×25 px)"
    )


def test_view_image_titles_show_scaled_viewport_pixels(
    window: MainWindow, make_pdf: MakePdf
) -> None:
    window.open_pdf(make_pdf([(200, 100)]))
    registry = commands.build_commands(window)
    viewport = window.page_view.viewport()
    w = round(viewport.width() * viewport.devicePixelRatioF())
    h = round(viewport.height() * viewport.devicePixelRatioF())
    assert commands.find(registry, commands.COPY_VIEW_IMAGE).display_title() == (
        f"Copy current view ({w}×{h} px)"
    )
    assert commands.find(registry, "copy_view_image_50").display_title() == (
        f"Copy current view at 50% ({round(w * 0.5)}×{round(h * 0.5)} px)"
    )


def test_display_title_defaults_to_title() -> None:
    cmd = Command("id", "static", lambda: None)
    assert cmd.display_title() == "static"
