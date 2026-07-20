"""A scrollable graphics view showing one rendered PDF page at a time.

The page is a background pixmap item; the edit controller adds movable
:class:`~app.gui.text_item.TextFieldItem` instances on top. The view stays a
pure view — it owns no field state, only the items currently on screen.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QEvent, QPointF, QRect, Qt, Signal
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
    QGraphicsScene,
    QGraphicsView,
)

from app.gui import page_view_grab, strings
from app.gui.image_item import ImageItem
from app.gui.item_layer import ItemLayer
from app.gui.page_highlights import PageHighlights
from app.gui.page_input import PageInputController
from app.gui.page_navigator import PageNavigator
from app.gui.page_overlay_items import OverlayItemsMixin
from app.gui.page_view_zoom import ZoomDelegateMixin
from app.gui.rect_item import RectItem
from app.gui.render_quality import RenderQualityController
from app.gui.selection_highlights import SelectionHighlights
from app.gui.text_item import TextFieldItem
from app.gui.zoom_controller import ZoomController

_OVERLAY_Z = 1.0  # default; per-item z (set from each spec) drives real stacking


class PageView(OverlayItemsMixin, ZoomDelegateMixin, QGraphicsView):
    """Renders the current page of an open PDF and tracks the page index."""

    page_changed = Signal(int, int)  # (current 1-based, total)
    page_will_change = Signal(int)  # (current 0-based index, before navigation)
    zoom_changed = Signal(int)  # current zoom percentage
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
        self._rect_layer: ItemLayer[RectItem] = ItemLayer(self._scene, _OVERLAY_Z)
        self._highlights = PageHighlights(self._scene)
        self._selection = SelectionHighlights(self._scene)
        # Consulted before the input controller; set by the select-mode controller
        # so vim-style keys intercept navigation/edit keys while that mode is on.
        self._key_interceptor: Callable[[QKeyEvent], bool] | None = None
        # Consulted before default click handling so select mode can place its
        # word cursor with the mouse; returns True when it consumes the click.
        self._click_handler: Callable[[QPointF], bool] | None = None
        self._nav = PageNavigator(self._show, self.page_will_change)
        # Re-render the page sharper as zoom changes; never moves overlay coords.
        self._render_ctl = RenderQualityController(self, self._pixmap_item)
        self._zoom_ctl = ZoomController(self, self._pixmap_item, self._on_zoom_scale)
        self._input = PageInputController(self)

    def _on_zoom_scale(self, scale: float) -> None:
        """Re-render sharp for the new scale and publish the zoom percentage."""
        self._render_ctl.request(scale)
        self.zoom_changed.emit(self._zoom_ctl.percent())

    # --- document lifecycle -------------------------------------------------

    def load(self, source: Path) -> None:
        """Open ``source`` and show its first page."""
        # Every fresh document starts un-suspended; an animated GIF re-arms after.
        self._render_ctl.set_suspended(False)
        self._nav.load(source)

    def reset(self) -> None:
        """Clear the open document and show the no-doc placeholder."""
        self._render_ctl.set_suspended(False)
        self.clear_text_items()
        self.clear_image_items()
        self.clear_rect_items()
        self.clear_highlights()
        self._pixmap_item.setPixmap(QPixmap())
        self._placeholder.setVisible(True)
        self._nav.clear()

    # --- animated GIF playback ----------------------------------------------

    def set_animating(self, on: bool) -> None:
        """Hide the placeholder and (un)suspend fitz re-render for movie playback."""
        if on:
            self._placeholder.setVisible(False)
        self._render_ctl.set_suspended(on)

    def is_render_suspended(self) -> bool:
        """Whether fitz re-render is paused (a movie is driving the page pixmap)."""
        return self._render_ctl.is_suspended()

    def show_animation_frame(self, pixmap: QPixmap) -> None:
        """Show one GIF frame; re-fit the scene only when the frame size changes."""
        resized = pixmap.size() != self._pixmap_item.pixmap().size()
        self._pixmap_item.setPixmap(pixmap)
        if resized:
            self._fit_scene_to_pixmap()

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

    # --- input hooks (select mode) ------------------------------------------

    def set_key_interceptor(self, interceptor: Callable[[QKeyEvent], bool] | None) -> None:
        """Install a hook consulted before the input controller for key presses."""
        self._key_interceptor = interceptor

    def set_click_handler(self, handler: Callable[[QPointF], bool] | None) -> None:
        """Install a hook consulted before default click handling (select mode)."""
        self._click_handler = handler

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

    def visible_page_rect(self) -> QRect:
        """Visible page area in viewport coords (see :mod:`app.gui.page_view_grab`)."""
        return page_view_grab.visible_page_rect(self)

    def grab_page_area(self) -> QPixmap:
        """Viewport grab clipped to the visible page (see :mod:`app.gui.page_view_grab`)."""
        return page_view_grab.grab_page_area(self)

    # --- custom text-field placement ----------------------------------------

    def begin_custom_placement(self, on_done: Callable[[QPointF | None], None]) -> None:
        """Show a draggable crosshair; call ``on_done`` with the chosen point or None."""
        self._input.begin_placement(on_done)

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
        if self._key_interceptor is not None and self._key_interceptor(event):
            event.accept()
            return
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
        if self._click_handler is not None and self._click_handler(
            self.mapToScene(event.position().toPoint())
        ):
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
        self._selection.clear()
        self._placeholder.setVisible(False)
        self._render_ctl.render_now()
        self._fit_scene_to_pixmap()
        self.page_changed.emit(self.current_page_one_based(), self._nav.total())

    def _fit_scene_to_pixmap(self) -> None:
        """Size the scene to the page pixmap and re-apply the zoom mode.

        Shared by ``_show`` (each page render) and ``show_animation_frame`` (each
        differently-sized GIF frame) so 100% stays 100% and fit re-fits.
        """
        self._scene.setSceneRect(self._pixmap_item.boundingRect())
        self._zoom_ctl.reapply()
