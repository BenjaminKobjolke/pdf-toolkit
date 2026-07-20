"""Document-centric command groups (open/save/copy, navigation, page ops, search).

Split out of :mod:`app.gui.commands` (which is at the file-length cap) and folded
into the registry by ``build_commands`` via a local import; the cycle is avoided
because ``commands`` imports this module only inside the function body.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING

from app.gui import commands as c
from app.gui import copy_image_titles, file_strings, release_strings, settings_strings, strings
from app.gui.commands import (
    COPY_IMAGE_PERCENTS,
    HAS_TEXT,
    PDF_ONLY,
    TRANSFORMABLE,
    VIEWABLE,
    Command,
    Predicate,
)

if TYPE_CHECKING:
    from app.gui.main_window import MainWindow


def document_commands(
    window: MainWindow, has_doc: Predicate, doc_in_view: Predicate
) -> list[Command]:
    """File and lifecycle commands.

    ``has_doc`` commands stay reachable while the thumbnails grid shows (they
    retarget to the selected thumbnail); ``doc_in_view`` commands need the
    loaded working copy on screen and hide while the grid covers it.
    """
    return [
        Command(c.OPEN, strings.CMD_OPEN, lambda: window.open_pdf()),
        Command(c.OPEN_DIR, strings.CMD_OPEN_DIR, window.open_directory),
        Command(c.OPEN_HISTORY, strings.CMD_OPEN_HISTORY, window.open_from_history),
        Command(
            c.OPEN_FOLDER_HISTORY,
            strings.CMD_OPEN_FOLDER_HISTORY,
            window.open_folder_from_history,
        ),
        # Format-agnostic (None): they never read the grid selection, so a
        # non-viewable selection must not hide them while the grid shows.
        Command(c.NEXT_FILE, strings.CMD_NEXT_FILE, window.open_next_file, has_doc),
        Command(c.PREV_FILE, strings.CMD_PREV_FILE, window.open_previous_file, has_doc),
        Command(c.SAVE, strings.CMD_SAVE, window.save_changes, doc_in_view, TRANSFORMABLE),
        Command(
            c.SAVE_AS,
            file_strings.CMD_SAVE_AS,
            window.document_actions.save_as,
            doc_in_view,
            TRANSFORMABLE,
        ),
        Command(
            c.COPY_FILE_PATH,
            file_strings.CMD_COPY_FILE_PATH,
            window.file_actions.copy_path,
            has_doc,
            VIEWABLE,
        ),
        Command(
            c.COPY_FILE_NAME,
            file_strings.CMD_COPY_FILE_NAME,
            window.file_actions.copy_name,
            has_doc,
            VIEWABLE,
        ),
        Command(
            c.COPY_FILE_NAME_NO_EXT,
            file_strings.CMD_COPY_FILE_NAME_NO_EXT,
            window.file_actions.copy_name_without_extension,
            has_doc,
            VIEWABLE,
        ),
        Command(
            c.COPY_PAGE_TEXT,
            file_strings.CMD_COPY_PAGE_TEXT,
            window.file_actions.copy_page_text,
            has_doc,
            HAS_TEXT,
        ),
        *(
            Command(
                c.COPY_PAGE_IMAGE if pct == 100 else f"{c.COPY_PAGE_IMAGE}_{pct}",
                copy_image_titles.static_page_title(pct),
                partial(window.file_actions.copy_page_image, pct / 100),
                has_doc,
                VIEWABLE,
                title_fn=partial(copy_image_titles.page_image_title, window, pct),
            )
            for pct in COPY_IMAGE_PERCENTS
        ),
        *(
            Command(
                c.COPY_VIEW_IMAGE if pct == 100 else f"{c.COPY_VIEW_IMAGE}_{pct}",
                copy_image_titles.static_view_title(pct),
                partial(window.file_actions.copy_view_image, pct / 100),
                doc_in_view,
                VIEWABLE,
                title_fn=partial(copy_image_titles.view_image_title, window, pct),
            )
            for pct in COPY_IMAGE_PERCENTS
        ),
        Command(
            c.OPEN_FOLDER,
            file_strings.CMD_OPEN_FOLDER,
            window.file_actions.open_folder,
            has_doc,
            VIEWABLE,
        ),
        Command(
            c.FILE_INFO,
            file_strings.CMD_FILE_INFO,
            window.file_info_actions.show,
            has_doc,
            VIEWABLE,
        ),
        Command(
            c.OPEN_WITH,
            file_strings.CMD_OPEN_WITH,
            window.open_with_actions.show,
            has_doc,
            VIEWABLE,
        ),
        Command(c.PRINT, strings.CMD_PRINT, window.print_actions.print_document, has_doc, VIEWABLE),
        Command(c.RENAME_FILE, strings.CMD_RENAME_FILE, window.rename_file, has_doc, VIEWABLE),
        Command(c.CLOSE_DOC, strings.CMD_CLOSE_DOC, window.close_document, doc_in_view, VIEWABLE),
        Command(
            c.RELOAD_DOC,
            settings_strings.CMD_RELOAD_DOC,
            window.reload_controller.reload,
            doc_in_view,
            VIEWABLE,
        ),
        Command(
            c.RELOAD_WATCH_SESSION,
            settings_strings.CMD_RELOAD_WATCH_SESSION,
            window.reload_controller.toggle_session_watch,
            doc_in_view,
            VIEWABLE,
        ),
        Command(
            c.RELOAD_WATCH_DEFAULT,
            settings_strings.CMD_RELOAD_WATCH_DEFAULT,
            window.reload_controller.toggle_watch_default,
        ),
        Command(c.EXIT, strings.CMD_EXIT, window.exit_app),
        Command(c.SHOW_SHORTCUTS, strings.CMD_SHOW_SHORTCUTS, window.show_keyboard_shortcuts),
        Command(c.RELEASE_NOTES, release_strings.CMD_RELEASE_NOTES, window.show_release_notes),
    ]


def navigation_commands(window: MainWindow, doc_in_view: Predicate) -> list[Command]:
    view = window.page_view
    return [
        Command(c.PREV_PAGE, strings.CMD_PREV_PAGE, view.show_prev, doc_in_view, VIEWABLE),
        Command(c.NEXT_PAGE, strings.CMD_NEXT_PAGE, view.show_next, doc_in_view, VIEWABLE),
        Command(c.FIRST_PAGE, strings.CMD_FIRST_PAGE, view.show_first, doc_in_view, VIEWABLE),
        Command(c.LAST_PAGE, strings.CMD_LAST_PAGE, view.show_last, doc_in_view, VIEWABLE),
    ]


def _thumb_or_page(
    window: MainWindow, thumb_fn: Callable[[], None], page_fn: Callable[[], None]
) -> Callable[[], None]:
    """Dispatch a zoom command to the thumbnails grid while it is showing."""
    from app.gui import effective_target

    return lambda: thumb_fn() if effective_target.grid_active(window) else page_fn()


def zoom_commands(window: MainWindow, has_doc: Predicate, doc_in_view: Predicate) -> list[Command]:
    view = window.page_view
    thumbs = window.thumbnails_controller
    return [
        Command(c.ZOOM_FIT, strings.CMD_ZOOM_FIT, view.zoom_fit, doc_in_view, VIEWABLE),
        Command(c.ZOOM_ACTUAL, strings.CMD_ZOOM_ACTUAL, view.zoom_actual, doc_in_view, VIEWABLE),
        # Format-agnostic + has_doc: redirected to thumbnail sizing while the
        # grid shows, so they must survive any (or no) selection.
        Command(
            c.ZOOM_IN,
            strings.CMD_ZOOM_IN,
            _thumb_or_page(window, thumbs.zoom_in, view.zoom_in),
            has_doc,
        ),
        Command(
            c.ZOOM_OUT,
            strings.CMD_ZOOM_OUT,
            _thumb_or_page(window, thumbs.zoom_out, view.zoom_out),
            has_doc,
        ),
    ]


def page_commands(window: MainWindow, doc_in_view: Predicate) -> list[Command]:
    pages = window.page_actions
    return [
        Command(c.SWAP, strings.CMD_SWAP, pages.swap, doc_in_view, PDF_ONLY),
        Command(
            c.DELETE_PAGE, strings.CMD_DELETE_PAGE, pages.delete_current_page, doc_in_view, PDF_ONLY
        ),
        Command(
            c.DELETE_RANGE, strings.CMD_DELETE_RANGE, pages.delete_page_range, doc_in_view, PDF_ONLY
        ),
        Command(c.INSERT_PAGE, strings.CMD_INSERT_PAGE, pages.insert_pages, doc_in_view, PDF_ONLY),
        Command(
            c.EXTRACT_PAGE,
            strings.CMD_EXTRACT_PAGE,
            pages.extract_current_page,
            doc_in_view,
            PDF_ONLY,
        ),
        # Merge is folder-bound (picks a folder, not the open doc); format handled inside the op.
        Command(c.MERGE_FOLDER, strings.CMD_MERGE_FOLDER, pages.merge_folder),
    ]


def rotate_commands(window: MainWindow, doc_in_view: Predicate) -> list[Command]:
    rotate = window.rotate_actions
    return [
        Command(
            c.ROTATE_LEFT, strings.CMD_ROTATE_LEFT, rotate.rotate_left, doc_in_view, TRANSFORMABLE
        ),
        Command(
            c.ROTATE_RIGHT,
            strings.CMD_ROTATE_RIGHT,
            rotate.rotate_right,
            doc_in_view,
            TRANSFORMABLE,
        ),
        Command(
            c.ROTATE_180, strings.CMD_ROTATE_180, rotate.rotate_180, doc_in_view, TRANSFORMABLE
        ),
        Command(
            c.FLIP_HORIZONTAL,
            strings.CMD_FLIP_HORIZONTAL,
            rotate.flip_horizontal,
            doc_in_view,
            TRANSFORMABLE,
        ),
        Command(
            c.FLIP_VERTICAL,
            strings.CMD_FLIP_VERTICAL,
            rotate.flip_vertical,
            doc_in_view,
            TRANSFORMABLE,
        ),
    ]


def move_commands(window: MainWindow, doc_in_view: Predicate) -> list[Command]:
    move = window.move_actions
    return [
        Command(c.MOVE_NEXT, strings.CMD_MOVE_NEXT, move.move_to_next, doc_in_view, PDF_ONLY),
        Command(c.MOVE_PREV, strings.CMD_MOVE_PREV, move.move_to_prev, doc_in_view, PDF_ONLY),
        Command(c.MOVE_FIRST, strings.CMD_MOVE_FIRST, move.move_to_first, doc_in_view, PDF_ONLY),
        Command(c.MOVE_LAST, strings.CMD_MOVE_LAST, move.move_to_last, doc_in_view, PDF_ONLY),
    ]


def search_commands(
    window: MainWindow, doc_in_view: Predicate, has_highlights: Predicate
) -> list[Command]:
    search = window.search_actions
    return [
        Command(
            c.SEARCH_PDF, strings.CMD_SEARCH_PDF, search.search_pdf_text, doc_in_view, HAS_TEXT
        ),
        Command(
            c.SEARCH_FIELDS, strings.CMD_SEARCH_FIELDS, search.search_fields, doc_in_view, PDF_ONLY
        ),
        Command(
            c.CLEAR_HIGHLIGHTS,
            strings.CMD_CLEAR_HIGHLIGHTS,
            search.clear_highlights,
            lambda: has_highlights() and doc_in_view(),
        ),
    ]
