"""A scrollable graphics view showing one rendered PDF page at a time.

The page is a background pixmap item; the edit controller adds movable
:class:`~app.gui.text_item.TextFieldItem` instances on top. The view stays a
pure view — it owns no field state, only the items currently on screen.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QKeyEvent, QPen, QPixmap, QWheelEvent
from PySide6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
)

from app.gui import render, strings
from app.gui.page_input import PageInputController
from app.gui.text_item import TextFieldItem
from app.gui.zoom_controller import ZoomController

_HIGHLIGHT_COLOR = "#ffd000"  # gold outline for search matches
_HIGHLIGHT_Z = 2.0  # above the page (0) and text items (1)


class PageView(QGraphicsView):
    """Renders the current page of an open PDF and tracks the page index."""

    page_changed = Signal(int, int)  # (current 1-based, total)
    page_will_change = Signal(int)  # (current 0-based index, before navigation)
    delete_requested = Signal()  # Delete/Backspace pressed on a selected field

    def __init__(self) -> None:
        super().__init__()
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pixmap_item = QGraphicsPixmapItem()
        self._pixmap_item.setZValue(0)
        self._scene.addItem(self._pixmap_item)
        self._placeholder = self._scene.addText(strings.LABEL_NO_DOC)
        self._text_items: list[TextFieldItem] = []
        self._highlight_items: list[QGraphicsRectItem] = []
        self._source: Path | None = None
        self._index = 0
        self._total = 0
        self._zoom_ctl = ZoomController(self, self._pixmap_item)
        self._input = PageInputController(self)

    # --- document lifecycle -------------------------------------------------

    def load(self, source: Path) -> None:
        """Open ``source`` and show its first page."""
        self._source = source
        self._total = render.page_count(source)
        self._index = 0
        self._show()

    def reset(self) -> None:
        """Clear the open document and show the no-doc placeholder."""
        self.clear_text_items()
        self.clear_highlights()
        self._pixmap_item.setPixmap(QPixmap())
        self._placeholder.setVisible(True)
        self._source = None
        self._index = 0
        self._total = 0

    def reload(self) -> None:
        """Re-render after the document changed, clamping the index if it shrank."""
        if self._source is None:
            return
        self._total = render.page_count(self._source)
        self._index = max(0, min(self._index, self._total - 1))
        self._show()

    def show_next(self) -> None:
        if self._source is not None and self._index < self._total - 1:
            self.page_will_change.emit(self._index)
            self._index += 1
            self._show()

    def show_prev(self) -> None:
        if self._source is not None and self._index > 0:
            self.page_will_change.emit(self._index)
            self._index -= 1
            self._show()

    def show_first(self) -> None:
        if self._source is not None and self._index != 0:
            self.page_will_change.emit(self._index)
            self._index = 0
            self._show()

    def show_last(self) -> None:
        last = self._total - 1
        if self._source is not None and self._index != last:
            self.page_will_change.emit(self._index)
            self._index = last
            self._show()

    def go_to_page(self, index: int) -> None:
        """Jump to absolute 0-based ``index`` (clamped to the page range)."""
        if self._source is None:
            return
        target = max(0, min(index, self._total - 1))
        if target != self._index:
            self.page_will_change.emit(self._index)
            self._index = target
            self._show()

    # --- search highlights --------------------------------------------------

    def set_highlights(self, rects_pts: list[tuple[float, float, float, float]]) -> None:
        """Draw gold outlines for the given match rects (in PDF points)."""
        self.clear_highlights()
        pen = QPen(QColor(_HIGHLIGHT_COLOR))
        pen.setWidth(2)
        z = render.DEFAULT_ZOOM
        for x0, y0, x1, y1 in rects_pts:
            item = self._scene.addRect(x0 * z, y0 * z, (x1 - x0) * z, (y1 - y0) * z, pen)
            item.setZValue(_HIGHLIGHT_Z)
            self._highlight_items.append(item)

    def clear_highlights(self) -> None:
        for item in self._highlight_items:
            self._scene.removeItem(item)
        self._highlight_items.clear()

    def has_highlights(self) -> bool:
        return bool(self._highlight_items)

    def highlight_items(self) -> tuple[QGraphicsRectItem, ...]:
        return tuple(self._highlight_items)

    # --- zoom (delegated to ZoomController) ---------------------------------

    def zoom(self) -> float:
        """Return the current scene-to-view scale factor."""
        return self._zoom_ctl.zoom()

    def zoom_actual(self) -> None:
        self._zoom_ctl.actual()

    def zoom_in(self) -> None:
        self._zoom_ctl.zoom_in()

    def zoom_out(self) -> None:
        self._zoom_ctl.zoom_out()

    def zoom_fit(self) -> None:
        if self._source is not None:
            self._zoom_ctl.fit()

    # --- queries ------------------------------------------------------------

    def current_page_one_based(self) -> int:
        return self._index + 1

    def current_page_index(self) -> int:
        """Return the displayed page index (0-based)."""
        return self._index

    def total_pages(self) -> int:
        return self._total

    def source(self) -> Path | None:
        """Return the open PDF path, or ``None`` when no document is loaded."""
        return self._source

    def graphics_scene(self) -> QGraphicsScene:
        """Expose the scene so the controller can watch it for changes."""
        return self._scene

    # --- text items ---------------------------------------------------------

    def add_text_item(self, item: TextFieldItem) -> None:
        item.setZValue(1)
        self._scene.addItem(item)
        self._text_items.append(item)

    def text_items(self) -> tuple[TextFieldItem, ...]:
        return tuple(self._text_items)

    def selected_text_item(self) -> TextFieldItem | None:
        """Return the first selected field on the current page, if any."""
        for item in self._text_items:
            if item.isSelected():
                return item
        return None

    def remove_text_item(self, item: TextFieldItem) -> None:
        if item in self._text_items:
            self._scene.removeItem(item)
            self._text_items.remove(item)

    def clear_text_items(self) -> None:
        for item in self._text_items:
            self._scene.removeItem(item)
        self._text_items.clear()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self._input.key_press(event):
            event.accept()
            return
        super().keyPressEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self._input.wheel(event):
            event.accept()
            return
        super().wheelEvent(event)

    # --- rendering ----------------------------------------------------------

    def _show(self) -> None:
        if self._source is None:
            return
        # Highlights belong to the page they were drawn on; drop them on render.
        self.clear_highlights()
        self._placeholder.setVisible(False)
        image = render.render_page(self._source, self._index)
        self._pixmap_item.setPixmap(QPixmap.fromImage(image))
        self._scene.setSceneRect(self._pixmap_item.boundingRect())
        # Re-apply the zoom mode so 100% stays 100% and fit re-fits each page.
        self._zoom_ctl.reapply()
        self.page_changed.emit(self.current_page_one_based(), self._total)
