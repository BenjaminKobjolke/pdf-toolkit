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

from app.gui import (
    default_app_strings,
    file_strings,
    link_strings,
    release_strings,
    select_strings,
    strings,
)
from app.os_integration import pdf_association
from app.pdf.file_format import TEXT_FORMATS, FileFormat

if TYPE_CHECKING:
    from app.gui.main_window import MainWindow

# Format-capability sets for annotating commands (self-describing: consumers ask
# a command which formats it supports rather than hardcoding per-format branches).
PDF_ONLY = frozenset({FileFormat.PDF})
VIEWABLE = PDF_ONLY | TEXT_FORMATS  # any rendered doc (pdf/txt/md)

# Command ids — stable keys for menu/shortcut lookups (UPPER_SNAKE_CASE).
OPEN = "open"
OPEN_HISTORY = "open_history"
NEXT_FILE = "next_file"
PREV_FILE = "prev_file"
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
SAVE_AS = "save_as"
COPY_FILE_PATH = "copy_file_path"
COPY_FILE_NAME = "copy_file_name"
COPY_FILE_NAME_NO_EXT = "copy_file_name_no_ext"
COPY_PAGE_TEXT = "copy_page_text"
OPEN_FOLDER = "open_folder"
PRINT = "print"
SHOW_SHORTCUTS = "show_shortcuts"
RELEASE_NOTES = "release_notes"
COMMAND_PALETTE = "command_palette"
CONFIGURE_SHORTCUTS = "configure_shortcuts"
SET_DEFAULT_PDF_VIEWER = "set_default_pdf_viewer"
REMOVE_PDF_HANDLER = "remove_pdf_handler"
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
TEXT_DARK_MODE = "text_dark_mode"
TEXT_FONT_SIZE = "text_font_size"
OPEN_FILTER_ALL_FILES = "open_filter_all_files"
OPEN_FILTER_EXTENSIONS = "open_filter_extensions"
ZOOM_SET_DEFAULT = "zoom_set_default"
DOC_ZOOM_REMEMBER = "doc_zoom_remember"
DOC_PAGE_REMEMBER = "doc_page_remember"
EDIT_MODE = "edit_mode"
SELECT_MODE = "select_mode"
OPEN_LINK = "open_link"
COPY_LINK = "copy_link"
LINK_FONT = "link_font"
LINK_TEXT_COLOR = "link_text_color"
LINK_BG_COLOR = "link_bg_color"
LINK_BOX_COLOR = "link_box_color"
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
    """One palette/menu/shortcut action.

    ``formats`` declares which document formats the command applies to; ``None``
    means format-agnostic (no open doc, or format-irrelevant, e.g. settings).
    """

    command_id: str
    title: str
    run: Callable[[], None]
    is_enabled: Callable[[], bool] = field(default=lambda: True)
    formats: frozenset[FileFormat] | None = None

    def available(self, fmt: FileFormat | None) -> bool:
        """Whether the command is reachable for a document of format ``fmt``."""
        if not self.is_enabled():
            return False
        return self.formats is None or (fmt is not None and fmt in self.formats)


Predicate = Callable[[], bool]


def build_commands(window: MainWindow) -> list[Command]:
    """Assemble the full registry from the per-concern command groups."""
    from app.gui import overlay_commands  # local import breaks the import cycle

    has_doc = window.has_document
    has_highlights = window.page_view.has_highlights
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
        *overlay_commands.field_commands(window),
        *overlay_commands.image_commands(window),
        *overlay_commands.rectangle_commands(window, has_doc),
        *overlay_commands.layer_commands(window),
    ]


def _document_commands(window: MainWindow, has_doc: Predicate) -> list[Command]:
    return [
        Command(OPEN, strings.CMD_OPEN, lambda: window.open_pdf()),
        Command(OPEN_HISTORY, strings.CMD_OPEN_HISTORY, window.open_from_history),
        Command(NEXT_FILE, strings.CMD_NEXT_FILE, window.open_next_file, has_doc, VIEWABLE),
        Command(PREV_FILE, strings.CMD_PREV_FILE, window.open_previous_file, has_doc, VIEWABLE),
        Command(SAVE, strings.CMD_SAVE, window.save_changes, has_doc, PDF_ONLY),
        Command(
            SAVE_AS, file_strings.CMD_SAVE_AS, window.document_actions.save_as, has_doc, PDF_ONLY
        ),
        Command(
            COPY_FILE_PATH,
            file_strings.CMD_COPY_FILE_PATH,
            window.file_actions.copy_path,
            has_doc,
            VIEWABLE,
        ),
        Command(
            COPY_FILE_NAME,
            file_strings.CMD_COPY_FILE_NAME,
            window.file_actions.copy_name,
            has_doc,
            VIEWABLE,
        ),
        Command(
            COPY_FILE_NAME_NO_EXT,
            file_strings.CMD_COPY_FILE_NAME_NO_EXT,
            window.file_actions.copy_name_without_extension,
            has_doc,
            VIEWABLE,
        ),
        Command(
            COPY_PAGE_TEXT,
            file_strings.CMD_COPY_PAGE_TEXT,
            window.file_actions.copy_page_text,
            has_doc,
            VIEWABLE,
        ),
        Command(
            OPEN_FOLDER,
            file_strings.CMD_OPEN_FOLDER,
            window.file_actions.open_folder,
            has_doc,
            VIEWABLE,
        ),
        Command(PRINT, strings.CMD_PRINT, window.print_actions.print_document, has_doc, VIEWABLE),
        Command(RENAME_FILE, strings.CMD_RENAME_FILE, window.rename_file, has_doc, VIEWABLE),
        Command(CLOSE_DOC, strings.CMD_CLOSE_DOC, window.close_document, has_doc, VIEWABLE),
        Command(EXIT, strings.CMD_EXIT, window.exit_app),
        Command(SHOW_SHORTCUTS, strings.CMD_SHOW_SHORTCUTS, window.show_keyboard_shortcuts),
        Command(RELEASE_NOTES, release_strings.CMD_RELEASE_NOTES, window.show_release_notes),
    ]


def _navigation_commands(window: MainWindow, has_doc: Predicate) -> list[Command]:
    view = window.page_view
    return [
        Command(PREV_PAGE, strings.CMD_PREV_PAGE, view.show_prev, has_doc, VIEWABLE),
        Command(NEXT_PAGE, strings.CMD_NEXT_PAGE, view.show_next, has_doc, VIEWABLE),
        Command(FIRST_PAGE, strings.CMD_FIRST_PAGE, view.show_first, has_doc, VIEWABLE),
        Command(LAST_PAGE, strings.CMD_LAST_PAGE, view.show_last, has_doc, VIEWABLE),
    ]


def _zoom_commands(window: MainWindow, has_doc: Predicate) -> list[Command]:
    view = window.page_view
    return [
        Command(ZOOM_FIT, strings.CMD_ZOOM_FIT, view.zoom_fit, has_doc, VIEWABLE),
        Command(ZOOM_ACTUAL, strings.CMD_ZOOM_ACTUAL, view.zoom_actual, has_doc, VIEWABLE),
        Command(ZOOM_IN, strings.CMD_ZOOM_IN, view.zoom_in, has_doc, VIEWABLE),
        Command(ZOOM_OUT, strings.CMD_ZOOM_OUT, view.zoom_out, has_doc, VIEWABLE),
    ]


def _page_commands(window: MainWindow, has_doc: Predicate) -> list[Command]:
    pages = window.page_actions
    return [
        Command(SWAP, strings.CMD_SWAP, pages.swap, has_doc, PDF_ONLY),
        Command(DELETE_PAGE, strings.CMD_DELETE_PAGE, pages.delete_current_page, has_doc, PDF_ONLY),
        Command(DELETE_RANGE, strings.CMD_DELETE_RANGE, pages.delete_page_range, has_doc, PDF_ONLY),
        Command(INSERT_PAGE, strings.CMD_INSERT_PAGE, pages.insert_pages, has_doc, PDF_ONLY),
        Command(
            EXTRACT_PAGE, strings.CMD_EXTRACT_PAGE, pages.extract_current_page, has_doc, PDF_ONLY
        ),
        # Merge is folder-bound (picks a folder, not the open doc); format handled inside the op.
        Command(MERGE_FOLDER, strings.CMD_MERGE_FOLDER, pages.merge_folder),
    ]


def _rotate_commands(window: MainWindow, has_doc: Predicate) -> list[Command]:
    rotate = window.rotate_actions
    return [
        Command(ROTATE_LEFT, strings.CMD_ROTATE_LEFT, rotate.rotate_left, has_doc, PDF_ONLY),
        Command(ROTATE_RIGHT, strings.CMD_ROTATE_RIGHT, rotate.rotate_right, has_doc, PDF_ONLY),
        Command(ROTATE_180, strings.CMD_ROTATE_180, rotate.rotate_180, has_doc, PDF_ONLY),
    ]


def _move_commands(window: MainWindow, has_doc: Predicate) -> list[Command]:
    move = window.move_actions
    return [
        Command(MOVE_NEXT, strings.CMD_MOVE_NEXT, move.move_to_next, has_doc, PDF_ONLY),
        Command(MOVE_PREV, strings.CMD_MOVE_PREV, move.move_to_prev, has_doc, PDF_ONLY),
        Command(MOVE_FIRST, strings.CMD_MOVE_FIRST, move.move_to_first, has_doc, PDF_ONLY),
        Command(MOVE_LAST, strings.CMD_MOVE_LAST, move.move_to_last, has_doc, PDF_ONLY),
    ]


def _view_commands(window: MainWindow) -> list[Command]:
    """Window chrome plus command-palette and outline appearance settings."""
    palette = window.palette_controller
    outline = window.outline_controller
    text_view = window.text_view_controller
    open_filter = window.open_filter_controller
    link = window.link_hint_settings
    zoom = window.zoom_settings_controller
    return [
        Command(COMMAND_PALETTE, strings.CMD_COMMAND_PALETTE, window.open_command_palette),
        Command(CONFIGURE_SHORTCUTS, strings.CMD_CONFIGURE_SHORTCUTS, window.configure_shortcuts),
        Command(
            SET_DEFAULT_PDF_VIEWER,
            default_app_strings.CMD_SET_DEFAULT_PDF_VIEWER,
            window.default_app_actions.set_as_default_pdf_viewer,
            pdf_association.is_supported,
        ),
        Command(
            REMOVE_PDF_HANDLER,
            default_app_strings.CMD_REMOVE_PDF_HANDLER,
            window.default_app_actions.remove_pdf_handler,
            pdf_association.is_supported,
        ),
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
        Command(
            TEXT_DARK_MODE,
            strings.CMD_TEXT_DARK_MODE,
            text_view.toggle_dark_mode,
            formats=TEXT_FORMATS,
        ),
        Command(
            TEXT_FONT_SIZE,
            strings.CMD_TEXT_FONT_SIZE,
            text_view.set_font_size,
            formats=TEXT_FORMATS,
        ),
        Command(
            OPEN_FILTER_ALL_FILES,
            strings.CMD_OPEN_FILTER_ALL_FILES,
            open_filter.toggle_all_files,
        ),
        Command(
            OPEN_FILTER_EXTENSIONS,
            strings.CMD_OPEN_FILTER_EXTENSIONS,
            open_filter.edit_extensions,
        ),
        Command(LINK_FONT, link_strings.CMD_LINK_FONT, link.set_font_size),
        Command(LINK_TEXT_COLOR, link_strings.CMD_LINK_TEXT_COLOR, link.set_text_color),
        Command(LINK_BG_COLOR, link_strings.CMD_LINK_BG_COLOR, link.set_background_color),
        Command(LINK_BOX_COLOR, link_strings.CMD_LINK_BOX_COLOR, link.set_box_color),
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
        Command(EDIT_MODE, strings.CMD_EDIT_MODE, window.toggle_edit_mode, has_doc, PDF_ONLY),
        Command(
            SELECT_MODE,
            select_strings.CMD_SELECT_MODE,
            window.toggle_select_mode,
            has_doc,
            VIEWABLE,
        ),
        Command(OPEN_LINK, link_strings.CMD_OPEN_LINK, window.open_link_hints, has_doc, VIEWABLE),
        Command(COPY_LINK, link_strings.CMD_COPY_LINK, window.copy_link_hints, has_doc, VIEWABLE),
        Command(
            SELECT_NEXT, strings.CMD_SELECT_NEXT, window.select_next_editable, has_doc, PDF_ONLY
        ),
        Command(
            SELECT_PREV, strings.CMD_SELECT_PREV, window.select_previous_editable, has_doc, PDF_ONLY
        ),
        Command(ADD_FIELD, strings.CMD_ADD_FIELD, window.add_text_field, has_doc, PDF_ONLY),
        Command(ADD_IMAGE, strings.CMD_ADD_IMAGE, window.add_image, has_doc, PDF_ONLY),
        Command(
            DELETE_FIELD, strings.CMD_DELETE_FIELD, controller.delete_selected, has_doc, PDF_ONLY
        ),
        Command(EXPORT_TEXT, strings.CMD_EXPORT_TEXT, window.export_text, has_doc, PDF_ONLY),
        Command(
            DELETE_SAVED_FIELDS,
            strings.CMD_DELETE_SAVED_FIELDS,
            window.delete_saved_text_fields,
            has_doc,
            PDF_ONLY,
        ),
    ]


def _search_commands(
    window: MainWindow, has_doc: Predicate, has_highlights: Predicate
) -> list[Command]:
    search = window.search_actions
    return [
        Command(SEARCH_PDF, strings.CMD_SEARCH_PDF, search.search_pdf_text, has_doc, VIEWABLE),
        Command(SEARCH_FIELDS, strings.CMD_SEARCH_FIELDS, search.search_fields, has_doc, PDF_ONLY),
        Command(
            CLEAR_HIGHLIGHTS, strings.CMD_CLEAR_HIGHLIGHTS, search.clear_highlights, has_highlights
        ),
    ]


def find(commands: list[Command], command_id: str) -> Command:
    """Return the command with ``command_id``; raises ``KeyError`` if absent."""
    for command in commands:
        if command.command_id == command_id:
            return command
    raise KeyError(command_id)
