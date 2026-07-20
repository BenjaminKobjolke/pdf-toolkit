"""Operation and file-action wiring for the main window.

Extracted from :mod:`app.gui.window_builder` (over the file-length cap),
mirroring the :mod:`app.gui.window_builder_memory` split. The file-centric
actions retarget to the selected thumbnail while the grid is showing (see
:mod:`app.gui.effective_target`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.config.open_with import OpenWithStore
from app.gui import effective_target
from app.gui.default_app_actions import DefaultAppActions
from app.gui.deferred_ops import DeferredOps
from app.gui.export_actions import ExportActions
from app.gui.file_actions import FileActions
from app.gui.file_info import FileInfoActions
from app.gui.move_actions import MoveActions
from app.gui.open_with import OpenWithActions
from app.gui.page_actions import PageActions
from app.gui.print_actions import PrintActions
from app.gui.rotate_actions import RotateActions
from app.gui.search_actions import SearchActions
from app.gui.thumbnails_controller import install_thumbnails

if TYPE_CHECKING:
    from app.gui.main_window import MainWindow


def build_operations(window: MainWindow) -> None:
    """Construct the thumbnails grid, document operations, and file actions."""
    install_thumbnails(window)
    window._export = ExportActions(
        window,
        window._controller,
        window._working_doc,
        window._save,
        window._page_view,
        window._report,
    )
    window._search_actions = SearchActions(
        window,
        window._page_view,
        window._controller,
        window._edit_bar,
        window._working_doc.working,
    )
    window._deferred = DeferredOps(
        window._runner,
        window._page_view,
        window._working_doc.working,
        window._save.mark_dirty,
        window._report,
    )
    window._page_actions = PageActions(
        window,
        window._deferred,
        window._runner,
        window.open_pdf,
        window._report,
        window._working_doc.original,
    )
    window._rotate_actions = RotateActions(window._deferred)
    window._move_actions = MoveActions(window._deferred)
    _build_file_actions(window)


def _build_file_actions(window: MainWindow) -> None:
    """Construct the file/info/open-with/print actions onto ``window``.

    While the thumbnails grid shows, these act on the selected thumbnail
    (effective_target); print falls back to the working copy.
    """
    window._print_actions = PrintActions(
        window,
        lambda: effective_target.grid_selection(window) or window._working_doc.working(),
    )
    window._default_app_actions = DefaultAppActions(window)
    window._file_actions = FileActions(
        window,
        lambda: effective_target.effective_source(window),
        window._report,
        lambda: effective_target.effective_page_index(window),
        window._page_view.grab_page_area,
    )
    window._file_info_actions = FileInfoActions(
        window,
        window._palette,
        lambda: effective_target.effective_source(window),
        lambda: effective_target.effective_page_index(window),
        window._report,
    )
    window._open_with_actions = OpenWithActions(
        window,
        window._palette,
        OpenWithStore(window._backend),
        lambda: effective_target.effective_source(window),
        window._report,
    )
