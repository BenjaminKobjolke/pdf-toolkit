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
EDIT_MODE = "edit_mode"
ADD_FIELD = "add_field"
DELETE_FIELD = "delete_field"
EXPORT_TEXT = "export_text"
DELETE_SAVED_FIELDS = "delete_saved_fields"


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
    has_doc = window.has_document

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
        Command(SWAP, strings.CMD_SWAP, window.swap_pages, has_doc),
        Command(DELETE_PAGE, strings.CMD_DELETE_PAGE, window.delete_current_page, has_doc),
        Command(DELETE_RANGE, strings.CMD_DELETE_RANGE, window.delete_page_range, has_doc),
        Command(MERGE_FOLDER, strings.CMD_MERGE_FOLDER, window.merge_folder),
        Command(EDIT_MODE, strings.CMD_EDIT_MODE, window.toggle_edit_mode, has_doc),
        Command(ADD_FIELD, strings.CMD_ADD_FIELD, controller.add_field, has_doc),
        Command(DELETE_FIELD, strings.CMD_DELETE_FIELD, controller.delete_selected, has_doc),
        Command(EXPORT_TEXT, strings.CMD_EXPORT_TEXT, window.export_text, has_doc),
        Command(
            DELETE_SAVED_FIELDS,
            strings.CMD_DELETE_SAVED_FIELDS,
            window.delete_saved_text_fields,
            has_doc,
        ),
    ]


def find(commands: list[Command], command_id: str) -> Command:
    """Return the command with ``command_id``; raises ``KeyError`` if absent."""
    for command in commands:
        if command.command_id == command_id:
            return command
    raise KeyError(command_id)
