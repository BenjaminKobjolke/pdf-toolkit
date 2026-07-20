"""Resolve which file a palette command acts on: grid selection or open document.

While the thumbnails grid is showing, file-centric commands target the selected
thumbnail; otherwise the open document. Free functions instead of MainWindow
methods so they stay unit-testable without a full window (and the accessors
file stays under the length cap).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from app.gui.main_window import MainWindow


def grid_active(window: MainWindow) -> bool:
    """True while the thumbnails grid is the visible view."""
    thumbnails = getattr(window, "_thumbnails", None)  # tolerate mid-assembly windows
    return thumbnails is not None and thumbnails.is_active()


def grid_selection(window: MainWindow) -> Path | None:
    """The selected thumbnail's path while the grid shows, else ``None``."""
    if not grid_active(window):
        return None
    return window._thumbnails.selected_path()


def effective_source(window: MainWindow) -> Path | None:
    """The file commands act on: the grid selection, else the open document."""
    return grid_selection(window) or window._source


def effective_page_index(window: MainWindow) -> int:
    """The page commands read: 0 for a grid selection (previews show page one)."""
    if grid_selection(window) is not None:
        return 0
    return window._page_view.current_page_index()


def doc_in_view(window: MainWindow) -> bool:
    """A document is open and the page view is showing it (grid not covering it)."""
    return window._source is not None and not grid_active(window)
