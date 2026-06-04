"""A scrollable graphics view showing one rendered PDF page at a time.

The page is a background pixmap item; the edit controller adds movable
:class:`~app.gui.text_item.TextFieldItem` instances on top. The view stays a
pure view — it owns no field state, only the items currently on screen.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QPixmap, QTransform
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QGraphicsView

from app.gui import render, strings
from app.gui.text_item import TextFieldItem

_NUDGE_STEP = 10.0  # scene px per arrow press
_NUDGE_STEP_FINE = 1.0  # scene px per arrow press while Shift is held
_ZOOM_IN_FACTOR = 1.1  # zoom in 10%
_ZOOM_OUT_FACTOR = 0.9  # zoom out 10%
# "100%" = true PDF size: the page is rendered at render.DEFAULT_ZOOM, so the
# view transform must divide that back out.
_ZOOM_ACTUAL = 1.0 / render.DEFAULT_ZOOM
_ARROW_DELTAS: dict[Qt.Key, tuple[float, float]] = {
    Qt.Key.Key_Left: (-1.0, 0.0),
    Qt.Key.Key_Right: (1.0, 0.0),
    Qt.Key.Key_Up: (0.0, -1.0),
    Qt.Key.Key_Down: (0.0, 1.0),
}


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
        self._source: Path | None = None
        self._index = 0
        self._total = 0
        self._zoom = _ZOOM_ACTUAL

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

    # --- zoom ---------------------------------------------------------------

    def zoom(self) -> float:
        """Return the current scene-to-view scale factor."""
        return self._zoom

    def zoom_actual(self) -> None:
        """Show the page at true PDF size (100%)."""
        self._apply_zoom(_ZOOM_ACTUAL)

    def zoom_in(self) -> None:
        self._apply_zoom(self._zoom * _ZOOM_IN_FACTOR)

    def zoom_out(self) -> None:
        self._apply_zoom(self._zoom * _ZOOM_OUT_FACTOR)

    def zoom_fit(self) -> None:
        """Scale the page to fit the viewport, preserving aspect ratio."""
        if self._source is None:
            return
        self.fitInView(self._pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        self._zoom = self.transform().m11()

    def _apply_zoom(self, scale: float) -> None:
        self._zoom = scale
        self.setTransform(QTransform().scale(scale, scale))

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

    def remove_text_item(self, item: TextFieldItem) -> None:
        if item in self._text_items:
            self._scene.removeItem(item)
            self._text_items.remove(item)

    def clear_text_items(self) -> None:
        for item in self._text_items:
            self._scene.removeItem(item)
        self._text_items.clear()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = Qt.Key(event.key())
        if key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace) and self._can_edit_selection():
            self.delete_requested.emit()
            event.accept()
            return
        if key in _ARROW_DELTAS and self._can_edit_selection() and self._nudge(event, key):
            event.accept()
            return
        super().keyPressEvent(event)

    def _nudge(self, event: QKeyEvent, key: Qt.Key) -> bool:
        """Move selected fields by an arrow step. Returns False if none selected."""
        selected = [item for item in self._text_items if item.isSelected()]
        if not selected:
            return False
        fine = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        step = _NUDGE_STEP_FINE if fine else _NUDGE_STEP
        dx, dy = _ARROW_DELTAS[key]
        for item in selected:
            item.moveBy(dx * step, dy * step)
        return True

    def _can_edit_selection(self) -> bool:
        """True when a field is selected and none is being text-edited."""
        focus = self._scene.focusItem()
        if isinstance(focus, TextFieldItem) and (
            focus.textInteractionFlags() != Qt.TextInteractionFlag.NoTextInteraction
        ):
            return False  # let the keystroke act on the text being edited
        return any(item.isSelected() for item in self._text_items)

    # --- rendering ----------------------------------------------------------

    def _show(self) -> None:
        if self._source is None:
            return
        self._placeholder.setVisible(False)
        image = render.render_page(self._source, self._index)
        self._pixmap_item.setPixmap(QPixmap.fromImage(image))
        self._scene.setSceneRect(self._pixmap_item.boundingRect())
        # Keep the view transform in sync with the stored zoom so it persists
        # across page changes and matches what zoom() reports.
        self.setTransform(QTransform().scale(self._zoom, self._zoom))
        self.page_changed.emit(self.current_page_one_based(), self._total)
