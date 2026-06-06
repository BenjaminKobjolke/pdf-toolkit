"""Document lifecycle and page navigation for the page view.

Owns the open source path, the current 0-based page index, and the page total.
The view supplies a ``render_current`` callback (run after each index change)
and its ``page_will_change`` signal (emitted before navigating); rendering stays
in the view, this only does the index bookkeeping.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from app.gui import render

if TYPE_CHECKING:
    from PySide6.QtCore import SignalInstance


class PageNavigator:
    """Tracks the open document and current page; drives re-render on change."""

    def __init__(
        self,
        render_current: Callable[[], None],
        page_will_change: SignalInstance,
    ) -> None:
        self._render = render_current
        self._page_will_change = page_will_change
        self._source: Path | None = None
        self._index = 0
        self._total = 0

    def source(self) -> Path | None:
        return self._source

    def index(self) -> int:
        """Current 0-based page index."""
        return self._index

    def total(self) -> int:
        return self._total

    def load(self, source: Path) -> None:
        """Open ``source`` and render its first page."""
        self._source = source
        self._total = render.page_count(source)
        self._index = 0
        self._render()

    def clear(self) -> None:
        """Forget the open document (the view clears the scene separately)."""
        self._source = None
        self._index = 0
        self._total = 0

    def reload(self) -> None:
        """Re-render after the document changed, clamping the index if it shrank."""
        if self._source is None:
            return
        self._total = render.page_count(self._source)
        self._index = max(0, min(self._index, self._total - 1))
        self._render()

    def show_next(self) -> None:
        if self._source is not None and self._index < self._total - 1:
            self._go(self._index + 1)

    def show_prev(self) -> None:
        if self._source is not None and self._index > 0:
            self._go(self._index - 1)

    def show_first(self) -> None:
        if self._source is not None and self._index != 0:
            self._go(0)

    def show_last(self) -> None:
        last = self._total - 1
        if self._source is not None and self._index != last:
            self._go(last)

    def go_to_page(self, index: int) -> None:
        """Jump to absolute 0-based ``index`` (clamped to the page range)."""
        if self._source is None:
            return
        target = max(0, min(index, self._total - 1))
        if target != self._index:
            self._go(target)

    def _go(self, index: int) -> None:
        self._page_will_change.emit(self._index)
        self._index = index
        self._render()
