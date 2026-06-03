"""A scrollable widget showing one rendered PDF page at a time."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QScrollArea

from app.gui import render, strings


class PageView(QScrollArea):
    """Renders the current page of an open PDF and tracks the page index."""

    page_changed = Signal(int, int)  # (current 1-based, total)

    def __init__(self) -> None:
        super().__init__()
        self._label = QLabel(strings.LABEL_NO_DOC)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWidget(self._label)
        self.setWidgetResizable(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._source: Path | None = None
        self._index = 0
        self._total = 0

    def load(self, source: Path) -> None:
        """Open ``source`` and show its first page."""
        self._source = source
        self._total = render.page_count(source)
        self._index = 0
        self._show()

    def reload(self) -> None:
        """Re-render after the document changed, clamping the index if it shrank."""
        if self._source is None:
            return
        self._total = render.page_count(self._source)
        self._index = max(0, min(self._index, self._total - 1))
        self._show()

    def show_next(self) -> None:
        if self._source is not None and self._index < self._total - 1:
            self._index += 1
            self._show()

    def show_prev(self) -> None:
        if self._source is not None and self._index > 0:
            self._index -= 1
            self._show()

    def current_page_one_based(self) -> int:
        """Return the displayed page number (1-based)."""
        return self._index + 1

    def total_pages(self) -> int:
        return self._total

    def _show(self) -> None:
        if self._source is None:
            return
        image = render.render_page(self._source, self._index)
        self._label.setPixmap(QPixmap.fromImage(image))
        self.page_changed.emit(self.current_page_one_based(), self._total)
