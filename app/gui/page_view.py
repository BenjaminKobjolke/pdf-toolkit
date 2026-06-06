"""A scrollable graphics view showing one rendered PDF page at a time.

The page is a background pixmap item; the edit controller adds movable
:class:`~app.gui.text_item.TextFieldItem` instances on top. The view stays a
pure view — it owns no field state, only the items currently on screen.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QEvent, QPointF, Qt, Signal
from PySide6.QtGui import QColor, QKeyEvent, QMouseEvent, QPen, QPixmap, QWheelEvent
from PySide6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
)

from app.gui import render, strings
from app.gui.image_item import ImageItem
from app.gui.item_layer import ItemLayer
from app.gui.page_input import PageInputController
from app.gui.text_item import TextFieldItem
from app.gui.zoom_controller import ZoomController

_OVERLAY_Z = 1.0  # text fields and images sit above the page (0)
_HIGHLIGHT_COLOR = "#ffd000"  # gold outline for search matches
_HIGHLIGHT_Z = 2.0  # above the page (0) and overlay items (1)


class PageView(QGraphicsView):
    """Renders the current page of an open PDF and tracks the page index."""

    page_changed = Signal(int, int)  # (current 1-based, total)
    page_will_change = Signal(int)  # (current 0-based index, before navigation)
    delete_requested = Signal()  # Delete/Backspace pressed on a selected field
    edit_text_requested = Signal()  # Enter pressed on a selected (not inline-editing) field

    def __init__(self) -> None:
        super().__init__()
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Track moves without a pressed button so the placement crosshair follows
        # the cursor; mouseMoveEvent ignores them unless placement is active.
        self.viewport().setMouseTracking(True)
        self._pixmap_item = QGraphicsPixmapItem()
        self._pixmap_item.setZValue(0)
        self._scene.addItem(self._pixmap_item)
        self._placeholder = self._scene.addText(strings.LABEL_NO_DOC)
        self._text_layer: ItemLayer[TextFieldItem] = ItemLayer(self._scene, _OVERLAY_Z)
        self._image_layer: ItemLayer[ImageItem] = ItemLayer(self._scene, _OVERLAY_Z)
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
        self.clear_image_items()
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

    def page_center(self) -> QPointF:
        """Return the centre of the page in scene pixels."""
        return self._scene.sceneRect().center()

    def viewport_center_scene(self) -> QPointF:
        """Return the centre of the visible viewport in scene pixels.

        Clamped to the page rect so a zoomed-out view (page smaller than the
        viewport) still yields a point on the page.
        """
        center = self.mapToScene(self.viewport().rect().center())
        rect = self._scene.sceneRect()
        x = min(max(center.x(), rect.left()), rect.right())
        y = min(max(center.y(), rect.top()), rect.bottom())
        return QPointF(x, y)

    # --- custom text-field placement ----------------------------------------

    def begin_custom_placement(self, on_done: Callable[[QPointF | None], None]) -> None:
        """Show a draggable crosshair; call ``on_done`` with the chosen point or None."""
        self._input.begin_placement(on_done)

    # --- text items ---------------------------------------------------------

    def add_text_item(self, item: TextFieldItem) -> None:
        self._text_layer.add(item)

    def text_items(self) -> tuple[TextFieldItem, ...]:
        return self._text_layer.items()

    def selected_text_item(self) -> TextFieldItem | None:
        """Return the first selected field on the current page, if any."""
        return self._text_layer.selected()

    def remove_text_item(self, item: TextFieldItem) -> None:
        self._text_layer.remove(item)

    def clear_text_items(self) -> None:
        self._text_layer.clear()

    # --- image items --------------------------------------------------------

    def add_image_item(self, item: ImageItem) -> None:
        self._image_layer.add(item)

    def image_items(self) -> tuple[ImageItem, ...]:
        return self._image_layer.items()

    def selected_image_item(self) -> ImageItem | None:
        """Return the first selected image on the current page, if any."""
        return self._image_layer.selected()

    def remove_image_item(self, item: ImageItem) -> None:
        self._image_layer.remove(item)

    def clear_image_items(self) -> None:
        self._image_layer.clear()

    def event(self, event: QEvent) -> bool:
        # Intercept Tab/Backtab before Qt's focus traversal swallows them, so they
        # cycle the editable overlay items instead of moving widget focus.
        if (
            event.type() == QEvent.Type.KeyPress
            and isinstance(event, QKeyEvent)
            and event.key() in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab)
            and self._input.key_press(event)
        ):
            return True
        return super().event(event)

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

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._input.placement_active():
            self._input.mouse_press(self.mapToScene(event.position().toPoint()))
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._input.placement_active():
            self._input.mouse_move(self.mapToScene(event.position().toPoint()))
            event.accept()
            return
        super().mouseMoveEvent(event)

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
