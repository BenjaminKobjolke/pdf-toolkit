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

from app.pdf.file_format import IMAGE_FORMATS, TEXT_FORMATS, FileFormat

if TYPE_CHECKING:
    from app.gui.main_window import MainWindow

# Format-capability sets for annotating commands (self-describing: consumers ask
# a command which formats it supports rather than hardcoding per-format branches).
PDF_ONLY = frozenset({FileFormat.PDF})
HAS_TEXT = PDF_ONLY | TEXT_FORMATS  # formats with extractable text (pdf/txt/md)
VIEWABLE = HAS_TEXT | IMAGE_FORMATS  # any rendered doc (pdf/txt/md/images)
# Rotate/flip mutate the working copy (for PSD a PNG conversion, so transforms
# are preview-only there; Save As exports that PNG).
TRANSFORMABLE = PDF_ONLY | IMAGE_FORMATS
# Save-to-original needs a writable original format; Pillow can't encode PSD.
SAVEABLE = PDF_ONLY | (IMAGE_FORMATS - {FileFormat.PSD})

# Command ids — stable keys for menu/shortcut lookups (UPPER_SNAKE_CASE).
OPEN = "open"
OPEN_DIR = "open_dir"
OPEN_HISTORY = "open_history"
OPEN_FOLDER_HISTORY = "open_folder_history"
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
FLIP_HORIZONTAL = "flip_horizontal"
FLIP_VERTICAL = "flip_vertical"
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
COPY_PAGE_IMAGE = "copy_page_image"
COPY_VIEW_IMAGE = "copy_view_image"
# Shared size steps for both copy-as-image families; 100% keeps the bare id,
# the rest get an "_<pct>" suffix (copy_page_image_50, copy_view_image_25, …).
COPY_IMAGE_PERCENTS = (100, 50, 25)
OPEN_FOLDER = "open_folder"
FILE_INFO = "file_info"
OPEN_WITH = "open_with"
PRINT = "print"
SHOW_SHORTCUTS = "show_shortcuts"
RELEASE_NOTES = "release_notes"
COMMAND_PALETTE = "command_palette"
CONFIGURE_SHORTCUTS = "configure_shortcuts"
FILE_TYPE_ASSOCIATIONS = "file_type_associations"
RENAME_FILE = "rename_file"
DELETE_FILE = "delete_file"
TOGGLE_MENU = "toggle_menu"
TOGGLE_TOOLBAR = "toggle_toolbar"
TOGGLE_STATUSBAR = "toggle_statusbar"
STATUSBAR_FONT = "statusbar_font"
TOGGLE_FULLSCREEN = "toggle_fullscreen"
THUMBNAILS_VIEW = "thumbnails_view"
FILTER_THUMBNAILS = "filter_thumbnails"
OPEN_FAVORITES_THUMBNAILS = "open_favorites_thumbnails"
GIF_TOGGLE = "gif_toggle"
PALETTE_WIDTH = "palette_width"
PALETTE_HEIGHT = "palette_height"
PALETTE_FONT = "palette_font"
PALETTE_OPACITY = "palette_opacity"
PALETTE_BORDERLESS = "palette_borderless"
DIALOG_SIZE = "dialog_size"
OUTLINE_WIDTH = "outline_width"
OUTLINE_STYLE = "outline_style"
OUTLINE_COLOR = "outline_color"
TEXT_DARK_MODE = "text_dark_mode"
TEXT_FONT_SIZE = "text_font_size"
OPEN_FILTER_ALL_FILES = "open_filter_all_files"
OPEN_FILTER_EXTENSIONS = "open_filter_extensions"
REUSE_WINDOW = "reuse_window"
FOCUS_ON_FORWARD = "focus_on_forward"
RELOAD_DOC = "reload_doc"
RELOAD_WATCH_SESSION = "reload_watch_session"
RELOAD_WATCH_DEFAULT = "reload_watch_default"
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
IMAGE_BACKGROUND = "image_background"
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
    title_fn: Callable[[], str] | None = None

    def available(self, fmt: FileFormat | None) -> bool:
        """Whether the command is reachable for a document of format ``fmt``."""
        if not self.is_enabled():
            return False
        return self.formats is None or (fmt is not None and fmt in self.formats)

    def display_title(self) -> str:
        """The palette row title — ``title_fn`` (live, e.g. pixel sizes) or ``title``."""
        return self.title_fn() if self.title_fn is not None else self.title


Predicate = Callable[[], bool]


def build_commands(window: MainWindow) -> list[Command]:
    """Assemble the full registry from the per-concern command groups."""
    # Local imports break the cycle: the group modules import from this module.
    from app.gui import doc_commands, effective_target, overlay_commands, view_commands

    has_doc = window.has_document
    has_highlights = window.page_view.has_highlights

    def has_target() -> bool:
        # File commands retarget to the selected thumbnail; a favorites-opened
        # grid has a selection but no open document.
        return effective_target.effective_source(window) is not None

    def doc_or_grid() -> bool:
        return window.has_document() or effective_target.grid_active(window)

    def doc_in_view() -> bool:
        # Commands needing the loaded working copy hide while the thumbnails
        # grid covers the page view; file commands retarget instead (see
        # effective_target).
        return effective_target.doc_in_view(window)

    return [
        *doc_commands.document_commands(window, has_doc, has_target, doc_in_view),
        *doc_commands.navigation_commands(window, doc_in_view),
        *doc_commands.zoom_commands(window, doc_or_grid, doc_in_view),
        *doc_commands.page_commands(window, doc_in_view),
        *doc_commands.rotate_commands(window, doc_in_view),
        *doc_commands.move_commands(window, doc_in_view),
        *view_commands.view_commands(window),
        *view_commands.edit_commands(window, has_target, doc_in_view),
        *doc_commands.search_commands(window, doc_in_view, has_highlights),
        *overlay_commands.field_commands(window),
        *overlay_commands.image_commands(window),
        *overlay_commands.rectangle_commands(window, has_doc),
        *overlay_commands.layer_commands(window),
    ]


def find(commands: list[Command], command_id: str) -> Command:
    """Return the command with ``command_id``; raises ``KeyError`` if absent."""
    for command in commands:
        if command.command_id == command_id:
            return command
    raise KeyError(command_id)
