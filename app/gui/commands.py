"""The single registry binding command ids to callbacks.

Menu items, keyboard shortcuts, and the command palette all resolve to the same
:class:`Command` here, so each action is wired exactly once. ``is_enabled``
decides whether a command shows in the palette / is reachable for the current
document state.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from app.gui import release_strings, strings

if TYPE_CHECKING:
    from app.gui.main_window import MainWindow

# Command ids — stable keys for menu/shortcut lookups (UPPER_SNAKE_CASE).
OPEN = "open"
OPEN_HISTORY = "open_history"
CLOSE_DOC = "close_doc"
EXIT = "exit"
PREV_PAGE = "prev_page"
NEXT_PAGE = "next_page"
FIRST_PAGE = "first_page"
LAST_PAGE = "last_page"
ZOOM_FIT = "zoom_fit"
ZOOM_ACTUAL = "zoom_actual"
ZOOM_IN = "zoom_in"
ZOOM_OUT = "zoom_out"
SWAP = "swap"
DELETE_PAGE = "delete_page"
DELETE_RANGE = "delete_range"
INSERT_PAGE = "insert_page"
EXTRACT_PAGE = "extract_page"
MERGE_FOLDER = "merge_folder"
ROTATE_LEFT = "rotate_left"
ROTATE_RIGHT = "rotate_right"
ROTATE_180 = "rotate_180"
MOVE_NEXT = "move_next"
MOVE_PREV = "move_prev"
MOVE_FIRST = "move_first"
MOVE_LAST = "move_last"
SAVE = "save"
PRINT = "print"
SHOW_SHORTCUTS = "show_shortcuts"
RELEASE_NOTES = "release_notes"
COMMAND_PALETTE = "command_palette"
CONFIGURE_SHORTCUTS = "configure_shortcuts"
RENAME_FILE = "rename_file"
TOGGLE_MENU = "toggle_menu"
TOGGLE_TOOLBAR = "toggle_toolbar"
TOGGLE_STATUSBAR = "toggle_statusbar"
TOGGLE_FULLSCREEN = "toggle_fullscreen"
PALETTE_WIDTH = "palette_width"
PALETTE_HEIGHT = "palette_height"
PALETTE_FONT = "palette_font"
PALETTE_OPACITY = "palette_opacity"
PALETTE_BORDERLESS = "palette_borderless"
OUTLINE_WIDTH = "outline_width"
OUTLINE_STYLE = "outline_style"
OUTLINE_COLOR = "outline_color"
ZOOM_SET_DEFAULT = "zoom_set_default"
DOC_ZOOM_REMEMBER = "doc_zoom_remember"
DOC_PAGE_REMEMBER = "doc_page_remember"
EDIT_MODE = "edit_mode"
SELECT_NEXT = "select_next"
SELECT_PREV = "select_prev"
ADD_FIELD = "add_field"
ADD_IMAGE = "add_image"
IMAGE_SCALE = "image_scale"
IMAGE_DELETE = "image_delete"
DELETE_FIELD = "delete_field"
EXPORT_TEXT = "export_text"
DELETE_SAVED_FIELDS = "delete_saved_fields"
REMEMBERED_SETTINGS = "remembered_settings"
SEARCH_PDF = "search_pdf"
SEARCH_FIELDS = "search_fields"
CLEAR_HIGHLIGHTS = "clear_highlights"
FIELD_CHANGE_TEXT = "field_change_text"
FIELD_FONT_SIZE = "field_font_size"
FIELD_FONT_FAMILY = "field_font_family"
FIELD_TEXT_COLOR = "field_text_color"
FIELD_BG_COLOR = "field_bg_color"
FIELD_TOGGLE_BOLD = "field_toggle_bold"
FIELD_TOGGLE_ITALIC = "field_toggle_italic"
FIELD_DELETE = "field_delete"


@dataclass(frozen=True)
class Command:
    """One palette/menu/shortcut action."""

    command_id: str
    title: str
    run: Callable[[], None]
    is_enabled: Callable[[], bool] = field(default=lambda: True)


Predicate = Callable[[], bool]


def build_commands(window: MainWindow) -> list[Command]:
    """Assemble the full registry from the per-concern command groups."""
    has_doc = window.has_document
    has_highlights = window.page_view.has_highlights
    has_field: Predicate = lambda: window.page_view.selected_text_item() is not None  # noqa: E731
    has_image: Predicate = lambda: window.page_view.selected_image_item() is not None  # noqa: E731
    return [
        *_document_commands(window, has_doc),
        *_navigation_commands(window, has_doc),
        *_zoom_commands(window, has_doc),
        *_page_commands(window, has_doc),
        *_rotate_commands(window, has_doc),
        *_move_commands(window, has_doc),
        *_view_commands(window),
        *_edit_commands(window, has_doc),
        *_search_commands(window, has_doc, has_highlights),
        *_field_commands(window, has_field),
        *_image_commands(window, has_image),
    ]


def _document_commands(window: MainWindow, has_doc: Predicate) -> list[Command]:
    return [
        Command(OPEN, strings.CMD_OPEN, lambda: window.open_pdf()),
        Command(OPEN_HISTORY, strings.CMD_OPEN_HISTORY, window.open_from_history),
        Command(SAVE, strings.CMD_SAVE, window.save_changes, has_doc),
        Command(PRINT, strings.CMD_PRINT, window.print_actions.print_document, has_doc),
        Command(RENAME_FILE, strings.CMD_RENAME_FILE, window.rename_file, has_doc),
        Command(CLOSE_DOC, strings.CMD_CLOSE_DOC, window.close_document, has_doc),
        Command(EXIT, strings.CMD_EXIT, window.exit_app),
        Command(SHOW_SHORTCUTS, strings.CMD_SHOW_SHORTCUTS, window.show_keyboard_shortcuts),
        Command(RELEASE_NOTES, release_strings.CMD_RELEASE_NOTES, window.show_release_notes),
    ]


def _navigation_commands(window: MainWindow, has_doc: Predicate) -> list[Command]:
    view = window.page_view
    return [
        Command(PREV_PAGE, strings.CMD_PREV_PAGE, view.show_prev, has_doc),
        Command(NEXT_PAGE, strings.CMD_NEXT_PAGE, view.show_next, has_doc),
        Command(FIRST_PAGE, strings.CMD_FIRST_PAGE, view.show_first, has_doc),
        Command(LAST_PAGE, strings.CMD_LAST_PAGE, view.show_last, has_doc),
    ]


def _zoom_commands(window: MainWindow, has_doc: Predicate) -> list[Command]:
    view = window.page_view
    return [
        Command(ZOOM_FIT, strings.CMD_ZOOM_FIT, view.zoom_fit, has_doc),
        Command(ZOOM_ACTUAL, strings.CMD_ZOOM_ACTUAL, view.zoom_actual, has_doc),
        Command(ZOOM_IN, strings.CMD_ZOOM_IN, view.zoom_in, has_doc),
        Command(ZOOM_OUT, strings.CMD_ZOOM_OUT, view.zoom_out, has_doc),
    ]


def _page_commands(window: MainWindow, has_doc: Predicate) -> list[Command]:
    pages = window.page_actions
    return [
        Command(SWAP, strings.CMD_SWAP, pages.swap, has_doc),
        Command(DELETE_PAGE, strings.CMD_DELETE_PAGE, pages.delete_current_page, has_doc),
        Command(DELETE_RANGE, strings.CMD_DELETE_RANGE, pages.delete_page_range, has_doc),
        Command(INSERT_PAGE, strings.CMD_INSERT_PAGE, pages.insert_pages, has_doc),
        Command(EXTRACT_PAGE, strings.CMD_EXTRACT_PAGE, pages.extract_current_page, has_doc),
        Command(MERGE_FOLDER, strings.CMD_MERGE_FOLDER, pages.merge_folder),
    ]


def _rotate_commands(window: MainWindow, has_doc: Predicate) -> list[Command]:
    rotate = window.rotate_actions
    return [
        Command(ROTATE_LEFT, strings.CMD_ROTATE_LEFT, rotate.rotate_left, has_doc),
        Command(ROTATE_RIGHT, strings.CMD_ROTATE_RIGHT, rotate.rotate_right, has_doc),
        Command(ROTATE_180, strings.CMD_ROTATE_180, rotate.rotate_180, has_doc),
    ]


def _move_commands(window: MainWindow, has_doc: Predicate) -> list[Command]:
    move = window.move_actions
    return [
        Command(MOVE_NEXT, strings.CMD_MOVE_NEXT, move.move_to_next, has_doc),
        Command(MOVE_PREV, strings.CMD_MOVE_PREV, move.move_to_prev, has_doc),
        Command(MOVE_FIRST, strings.CMD_MOVE_FIRST, move.move_to_first, has_doc),
        Command(MOVE_LAST, strings.CMD_MOVE_LAST, move.move_to_last, has_doc),
    ]


def _view_commands(window: MainWindow) -> list[Command]:
    """Window chrome plus command-palette and outline appearance settings."""
    palette = window.palette_controller
    outline = window.outline_controller
    zoom = window.zoom_settings_controller
    return [
        Command(COMMAND_PALETTE, strings.CMD_COMMAND_PALETTE, window.open_command_palette),
        Command(CONFIGURE_SHORTCUTS, strings.CMD_CONFIGURE_SHORTCUTS, window.configure_shortcuts),
        Command(TOGGLE_MENU, strings.CMD_TOGGLE_MENU, window.toggle_menu_bar),
        Command(TOGGLE_TOOLBAR, strings.CMD_TOGGLE_TOOLBAR, window.toggle_toolbar),
        Command(TOGGLE_STATUSBAR, strings.CMD_TOGGLE_STATUSBAR, window.toggle_statusbar),
        Command(TOGGLE_FULLSCREEN, strings.CMD_TOGGLE_FULLSCREEN, window.toggle_fullscreen),
        Command(PALETTE_WIDTH, strings.CMD_PALETTE_WIDTH, palette.set_width),
        Command(PALETTE_HEIGHT, strings.CMD_PALETTE_HEIGHT, palette.set_height),
        Command(PALETTE_FONT, strings.CMD_PALETTE_FONT, palette.set_font_size),
        Command(PALETTE_OPACITY, strings.CMD_PALETTE_OPACITY, palette.set_opacity),
        Command(PALETTE_BORDERLESS, strings.CMD_PALETTE_BORDERLESS, palette.toggle_borderless),
        Command(OUTLINE_WIDTH, strings.CMD_OUTLINE_WIDTH, outline.set_width),
        Command(OUTLINE_STYLE, strings.CMD_OUTLINE_STYLE, outline.set_style),
        Command(OUTLINE_COLOR, strings.CMD_OUTLINE_COLOR, outline.set_color),
        Command(ZOOM_SET_DEFAULT, strings.CMD_SET_DEFAULT_ZOOM, zoom.set_default_zoom),
        Command(DOC_ZOOM_REMEMBER, strings.CMD_REMEMBER_DOC_ZOOM, window.remember_document_zoom),
        Command(DOC_PAGE_REMEMBER, strings.CMD_REMEMBER_DOC_PAGE, window.remember_document_page),
        Command(
            REMEMBERED_SETTINGS,
            strings.CMD_REMEMBERED_SETTINGS,
            window.open_remembered_settings,
        ),
    ]


def _edit_commands(window: MainWindow, has_doc: Predicate) -> list[Command]:
    controller = window.controller
    return [
        Command(EDIT_MODE, strings.CMD_EDIT_MODE, window.toggle_edit_mode, has_doc),
        Command(SELECT_NEXT, strings.CMD_SELECT_NEXT, window.select_next_editable, has_doc),
        Command(SELECT_PREV, strings.CMD_SELECT_PREV, window.select_previous_editable, has_doc),
        Command(ADD_FIELD, strings.CMD_ADD_FIELD, window.add_text_field, has_doc),
        Command(ADD_IMAGE, strings.CMD_ADD_IMAGE, window.add_image, has_doc),
        Command(DELETE_FIELD, strings.CMD_DELETE_FIELD, controller.delete_selected, has_doc),
        Command(EXPORT_TEXT, strings.CMD_EXPORT_TEXT, window.export_text, has_doc),
        Command(
            DELETE_SAVED_FIELDS,
            strings.CMD_DELETE_SAVED_FIELDS,
            window.delete_saved_text_fields,
            has_doc,
        ),
    ]


def _image_commands(window: MainWindow, has_image: Predicate) -> list[Command]:
    """Commands shown only while an image is selected."""
    images = window.image_actions
    return [
        Command(IMAGE_SCALE, strings.CMD_IMAGE_SCALE, images.change_scale, has_image),
        Command(IMAGE_DELETE, strings.CMD_IMAGE_DELETE, images.delete, has_image),
    ]


def _search_commands(
    window: MainWindow, has_doc: Predicate, has_highlights: Predicate
) -> list[Command]:
    search = window.search_actions
    return [
        Command(SEARCH_PDF, strings.CMD_SEARCH_PDF, search.search_pdf_text, has_doc),
        Command(SEARCH_FIELDS, strings.CMD_SEARCH_FIELDS, search.search_fields, has_doc),
        Command(
            CLEAR_HIGHLIGHTS, strings.CMD_CLEAR_HIGHLIGHTS, search.clear_highlights, has_highlights
        ),
    ]


def _field_commands(window: MainWindow, has_field: Predicate) -> list[Command]:
    """Commands shown only while a text field is selected."""
    fields = window.field_actions
    return [
        Command(FIELD_CHANGE_TEXT, strings.CMD_FIELD_CHANGE_TEXT, fields.change_text, has_field),
        Command(FIELD_FONT_SIZE, strings.CMD_FIELD_FONT_SIZE, fields.change_size, has_field),
        Command(FIELD_FONT_FAMILY, strings.CMD_FIELD_FONT_FAMILY, fields.change_font, has_field),
        Command(
            FIELD_TEXT_COLOR, strings.CMD_FIELD_TEXT_COLOR, fields.change_text_color, has_field
        ),
        Command(FIELD_BG_COLOR, strings.CMD_FIELD_BG_COLOR, fields.change_bg_color, has_field),
        Command(FIELD_TOGGLE_BOLD, strings.CMD_FIELD_TOGGLE_BOLD, fields.toggle_bold, has_field),
        Command(
            FIELD_TOGGLE_ITALIC, strings.CMD_FIELD_TOGGLE_ITALIC, fields.toggle_italic, has_field
        ),
        Command(FIELD_DELETE, strings.CMD_FIELD_DELETE, fields.delete, has_field),
    ]


def find(commands: list[Command], command_id: str) -> Command:
    """Return the command with ``command_id``; raises ``KeyError`` if absent."""
    for command in commands:
        if command.command_id == command_id:
            return command
    raise KeyError(command_id)
