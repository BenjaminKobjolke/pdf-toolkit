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

from app.gui import strings

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
MERGE_FOLDER = "merge_folder"
RENAME_FILE = "rename_file"
TOGGLE_MENU = "toggle_menu"
TOGGLE_TOOLBAR = "toggle_toolbar"
EDIT_MODE = "edit_mode"
ADD_FIELD = "add_field"
DELETE_FIELD = "delete_field"
EXPORT_TEXT = "export_text"
DELETE_SAVED_FIELDS = "delete_saved_fields"
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


def build_commands(window: MainWindow) -> list[Command]:
    """Build the full command registry bound to ``window`` and its collaborators."""
    view = window.page_view
    controller = window.controller
    fields = window.field_actions
    search = window.search_actions
    pages = window.page_actions
    has_doc = window.has_document
    has_highlights = view.has_highlights
    has_field = lambda: view.selected_text_item() is not None  # noqa: E731

    return [
        Command(OPEN, strings.CMD_OPEN, lambda: window.open_pdf()),
        Command(OPEN_HISTORY, strings.CMD_OPEN_HISTORY, window.open_from_history),
        Command(CLOSE_DOC, strings.CMD_CLOSE_DOC, window.close_document, has_doc),
        Command(EXIT, strings.CMD_EXIT, window.exit_app),
        Command(PREV_PAGE, strings.CMD_PREV_PAGE, view.show_prev, has_doc),
        Command(NEXT_PAGE, strings.CMD_NEXT_PAGE, view.show_next, has_doc),
        Command(FIRST_PAGE, strings.CMD_FIRST_PAGE, view.show_first, has_doc),
        Command(LAST_PAGE, strings.CMD_LAST_PAGE, view.show_last, has_doc),
        Command(ZOOM_FIT, strings.CMD_ZOOM_FIT, view.zoom_fit, has_doc),
        Command(ZOOM_ACTUAL, strings.CMD_ZOOM_ACTUAL, view.zoom_actual, has_doc),
        Command(ZOOM_IN, strings.CMD_ZOOM_IN, view.zoom_in, has_doc),
        Command(ZOOM_OUT, strings.CMD_ZOOM_OUT, view.zoom_out, has_doc),
        Command(SWAP, strings.CMD_SWAP, pages.swap, has_doc),
        Command(DELETE_PAGE, strings.CMD_DELETE_PAGE, pages.delete_current_page, has_doc),
        Command(DELETE_RANGE, strings.CMD_DELETE_RANGE, pages.delete_page_range, has_doc),
        Command(MERGE_FOLDER, strings.CMD_MERGE_FOLDER, pages.merge_folder),
        Command(RENAME_FILE, strings.CMD_RENAME_FILE, window.rename_file, has_doc),
        Command(TOGGLE_MENU, strings.CMD_TOGGLE_MENU, window.toggle_menu_bar),
        Command(TOGGLE_TOOLBAR, strings.CMD_TOGGLE_TOOLBAR, window.toggle_toolbar),
        Command(EDIT_MODE, strings.CMD_EDIT_MODE, window.toggle_edit_mode, has_doc),
        Command(ADD_FIELD, strings.CMD_ADD_FIELD, window.add_text_field, has_doc),
        Command(DELETE_FIELD, strings.CMD_DELETE_FIELD, controller.delete_selected, has_doc),
        Command(EXPORT_TEXT, strings.CMD_EXPORT_TEXT, window.export_text, has_doc),
        Command(
            DELETE_SAVED_FIELDS,
            strings.CMD_DELETE_SAVED_FIELDS,
            window.delete_saved_text_fields,
            has_doc,
        ),
        Command(SEARCH_PDF, strings.CMD_SEARCH_PDF, search.search_pdf_text, has_doc),
        Command(SEARCH_FIELDS, strings.CMD_SEARCH_FIELDS, search.search_fields, has_doc),
        Command(
            CLEAR_HIGHLIGHTS, strings.CMD_CLEAR_HIGHLIGHTS, search.clear_highlights, has_highlights
        ),
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
