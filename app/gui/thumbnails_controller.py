"""State and policy for the thumbnails view.

Owns whether the grid is showing (the main window swaps the page view and the
grid inside one ``QStackedWidget``), the remembered thumbnail size, and the
±10% size stepping the redirected zoom commands drive while the grid is
active. The Qt grid widget itself lives in :mod:`app.gui.thumbnails_view`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from app.config.thumbnail_settings import ThumbnailSettings, clamp_thumb_size
from app.gui import file_browser_model

if TYPE_CHECKING:
    from PySide6.QtWidgets import QStackedWidget

    from app.config.thumbnail_settings import ThumbnailSettingsStore
    from app.gui.file_browser_model import FileFilter
    from app.gui.main_window import MainWindow
    from app.gui.page_view import PageView
    from app.gui.thumbnails_view import ThumbnailsView

# Same relative step as the page-zoom commands the grid borrows.
_STEP = 1.1


@dataclass
class ThumbnailsController:
    """Toggle the grid in and out of the view stack and step its thumbnail size."""

    store: ThumbnailSettingsStore
    stack: QStackedWidget
    page_view: PageView
    view: ThumbnailsView
    source: Callable[[], Path | None]
    current_filter: Callable[[], FileFilter]
    open_file: Callable[[Path], None]
    _active: bool = field(default=False, init=False)
    _size: int = field(init=False)

    def __post_init__(self) -> None:
        self._size = self.store.load().size

    def is_active(self) -> bool:
        """True while the grid is the visible widget in the stack."""
        return self._active

    def toggle(self) -> None:
        """Show the grid if hidden, return to the page view if showing."""
        if self._active:
            self.leave()
        else:
            self.enter()

    def enter(self) -> None:
        """Swap the grid in, listing the current document's directory."""
        current = self.source()
        if current is None:
            return
        paths = file_browser_model.openable_files(current.parent, self.current_filter())
        self._show(paths, current)

    def enter_directory(self, directory: Path) -> bool:
        """Swap the grid in for ``directory``; ``False`` when nothing is openable.

        Unlike :meth:`enter` this needs no open document — the first file in the
        listing starts selected.
        """
        paths = file_browser_model.openable_files(directory, self.current_filter())
        if not paths:
            return False
        self._show(paths, paths[0])
        return True

    def _show(self, paths: list[Path], current: Path) -> None:
        # An overlay item selected in edit mode would keep the Ctrl+arrow keys
        # bound to item scaling (window_input._zoom_or_scale) instead of the
        # redirected zoom commands.
        self.page_view.graphics_scene().clearSelection()
        self.view.clear_filter()
        self.view.set_thumb_size(self._size)
        self.view.populate(paths, current)
        self.stack.setCurrentWidget(self.view)
        self.view.setFocus()
        self._active = True

    def start_filter(self) -> None:
        """Begin filter mode, entering the grid first when it is hidden."""
        if not self._active:
            self.enter()
        if self._active:
            self.view.start_filter()

    def leave(self) -> None:
        """Swap the page view back in; no-op while the grid is not showing."""
        if not self._active:
            return
        self._active = False
        self.stack.setCurrentWidget(self.page_view)
        self.page_view.setFocus()

    def selected_path(self) -> Path | None:
        """Path of the highlighted thumbnail while the grid shows, else ``None``."""
        if not self._active:
            return None
        return self.view.selected_path()

    def refresh(self, select: Path | None = None) -> None:
        """Re-list the directory and repopulate, selecting ``select`` (or keeping it).

        No-op while the grid is hidden. Used after an on-disk change (e.g. a
        rename from the palette) so the grid reflects the new listing without
        leaving it.
        """
        if not self._active:
            return
        current = select or self.selected_path() or self.source()
        if current is None:
            return
        paths = file_browser_model.openable_files(current.parent, self.current_filter())
        self.view.populate(paths, current)

    def open_selected(self, path: Path) -> None:
        """Leave the grid and open ``path`` in the regular viewer."""
        self.leave()
        self.open_file(path)

    def zoom_in(self) -> None:
        """Grow thumbnails by 10% (clamped), persisting the new size."""
        self._apply_size(round(self._size * _STEP))

    def zoom_out(self) -> None:
        """Shrink thumbnails by 10% (clamped), persisting the new size."""
        self._apply_size(round(self._size / _STEP))

    def _apply_size(self, size: int) -> None:
        self._size = clamp_thumb_size(size)
        self.store.save(ThumbnailSettings(size=self._size))
        self.view.set_thumb_size(self._size)


def install_thumbnails(window: MainWindow) -> None:
    """Create the grid, the page/grid view stack, and the controller on ``window``.

    Extracted from :mod:`app.gui.window_builder` (over the file-length cap);
    local imports keep this module import-light for the unit tests.
    """
    from PySide6.QtWidgets import QLabel, QStackedWidget

    from app.config.thumbnail_settings import ThumbnailSettingsStore
    from app.gui import thumbnail_strings
    from app.gui.thumbnails_view import ThumbnailsView

    window._thumbnails_view = ThumbnailsView()
    window._thumb_filter_label = QLabel()
    window._thumb_filter_label.setContentsMargins(8, 2, 8, 2)  # matches ModeStatusBar
    window._thumb_filter_label.hide()

    def _show_filter(text: str) -> None:
        window._thumb_filter_label.setText(thumbnail_strings.FILTER_FMT.format(text=text))

    window._thumbnails_view.filter_changed.connect(_show_filter)
    window._thumbnails_view.filter_mode_changed.connect(window._thumb_filter_label.setVisible)
    window._view_stack = QStackedWidget()
    window._view_stack.addWidget(window._page_view)
    window._view_stack.addWidget(window._thumbnails_view)
    window._thumbnails = ThumbnailsController(
        store=ThumbnailSettingsStore(window._backend),
        stack=window._view_stack,
        page_view=window._page_view,
        view=window._thumbnails_view,
        source=lambda: window._source,
        current_filter=lambda: window._open_filter.current_filter(),
        open_file=window.open_pdf,
    )
    window._thumbnails_view.open_requested.connect(window._thumbnails.open_selected)
    window._thumbnails_view.dismiss_requested.connect(window._thumbnails.leave)
