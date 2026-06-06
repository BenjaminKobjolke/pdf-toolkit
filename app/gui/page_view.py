"""A scrollable graphics view showing one rendered PDF page at a time.

The page is a background pixmap item; the edit controller adds movable
:class:`~app.gui.text_item.TextFieldItem` instances on top. The view stays a
pure view — it owns no field state, only the items currently on screen.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QEvent, QPointF, Qt, Signal
from PySide6.QtGui import (
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPixmap,
    QResizeEvent,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
)

from app.gui import strings
from app.gui.image_item import ImageItem
from app.gui.item_layer import ItemLayer
from app.gui.page_highlights import PageHighlights
from app.gui.page_input import PageInputController
from app.gui.page_navigator import PageNavigator
from app.gui.render_quality import RenderQualityController
from app.gui.text_item import TextFieldItem
from app.gui.zoom_controller import ZoomController

_OVERLAY_Z = 1.0  # text fields and images sit above the page (0)


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
        # Smooth any scaling between re-renders and antialias highlight outlines.
        self.setRenderHints(
            QPainter.RenderHint.SmoothPixmapTransform | QPainter.RenderHint.Antialiasing
        )
        # Track moves without a pressed button so the placement crosshair follows
        # the cursor; mouseMoveEvent ignores them unless placement is active.
        self.viewport().setMouseTracking(True)
        self._pixmap_item = QGraphicsPixmapItem()
        self._pixmap_item.setZValue(0)
        self._scene.addItem(self._pixmap_item)
        self._placeholder = self._scene.addText(strings.LABEL_NO_DOC)
        self._text_layer: ItemLayer[TextFieldItem] = ItemLayer(self._scene, _OVERLAY_Z)
        self._image_layer: ItemLayer[ImageItem] = ItemLayer(self._scene, _OVERLAY_Z)
        self._highlights = PageHighlights(self._scene)
        self._nav = PageNavigator(self._show, self.page_will_change)
        # Re-render the page sharper as zoom changes; never moves overlay coords.
        self._render_ctl = RenderQualityController(self, self._pixmap_item)
        self._zoom_ctl = ZoomController(self, self._pixmap_item, self._render_ctl.request)
        self._input = PageInputController(self)

    # --- document lifecycle -------------------------------------------------

    def load(self, source: Path) -> None:
        """Open ``source`` and show its first page."""
        self._nav.load(source)

    def reset(self) -> None:
        """Clear the open document and show the no-doc placeholder."""
        self.clear_text_items()
        self.clear_image_items()
        self.clear_highlights()
        self._pixmap_item.setPixmap(QPixmap())
        self._placeholder.setVisible(True)
        self._nav.clear()

    def reload(self) -> None:
        """Re-render after the document changed, clamping the index if it shrank."""
        self._nav.reload()

    def show_next(self) -> None:
        self._nav.show_next()

    def show_prev(self) -> None:
        self._nav.show_prev()

    def show_first(self) -> None:
        self._nav.show_first()

    def show_last(self) -> None:
        self._nav.show_last()

    def go_to_page(self, index: int) -> None:
        """Jump to absolute 0-based ``index`` (clamped to the page range)."""
        self._nav.go_to_page(index)

    # --- search highlights --------------------------------------------------

    def set_highlights(self, rects_pts: list[tuple[float, float, float, float]]) -> None:
        """Draw gold outlines for the given match rects (in PDF points)."""
        self._highlights.set(rects_pts)

    def clear_highlights(self) -> None:
        self._highlights.clear()

    def has_highlights(self) -> bool:
        return self._highlights.has()

    def highlight_items(self) -> tuple[QGraphicsRectItem, ...]:
        return self._highlights.items()

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
        if self._nav.source() is not None:
            self._zoom_ctl.fit()

    def set_default_zoom(self, fit: bool, percent: int) -> None:
        """Set the start zoom mode; apply it now if a document is already open."""
        self._zoom_ctl.set_default(fit, percent)
        if self._nav.source() is not None:
            self._zoom_ctl.reapply()

    # --- queries ------------------------------------------------------------

    def current_page_one_based(self) -> int:
        return self._nav.index() + 1

    def current_page_index(self) -> int:
        """Return the displayed page index (0-based)."""
        return self._nav.index()

    def total_pages(self) -> int:
        return self._nav.total()

    def source(self) -> Path | None:
        """Return the open PDF path, or ``None`` when no document is loaded."""
        return self._nav.source()

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

    def resizeEvent(self, event: QResizeEvent) -> None:
        # Fit mode depends on the viewport size, so re-fit when it changes. This
        # also fixes the initial fit: the view is first sized only after the
        # window is shown, which happens after the document already loaded.
        super().resizeEvent(event)
        if self._nav.source() is not None:
            self._zoom_ctl.reapply()

    # --- rendering ----------------------------------------------------------

    def _show(self) -> None:
        if self._nav.source() is None:
            return
        # Highlights belong to the page they were drawn on; drop them on render.
        self.clear_highlights()
        self._placeholder.setVisible(False)
        self._render_ctl.render_now()
        self._scene.setSceneRect(self._pixmap_item.boundingRect())
        # Re-apply the zoom mode so 100% stays 100% and fit re-fits each page.
        self._zoom_ctl.reapply()
        self.page_changed.emit(self.current_page_one_based(), self._nav.total())
