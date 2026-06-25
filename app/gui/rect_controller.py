"""Owns the rectangle side of the editing model: per-page items, harvest/restore.

Parallel to :class:`~app.gui.image_controller.ImageController`: it does NOT
persist (the shared :class:`PageItemStore` and the single autosave timer live in
``EditController``, which writes all kinds in one save). It only manages the live
rect items on the page and keeps the store's rect dict in sync on navigation, add,
delete, and resize.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QPointF

from app.gui import rect_style
from app.gui.overlay_selection import place_new_item
from app.gui.page_item_store import PageItemStore
from app.gui.page_view import PageView


class RectController:
    """Coordinates placed rectangles between the page view and the shared store."""

    def __init__(
        self, page_view: PageView, store: PageItemStore, schedule_autosave: Callable[[], None]
    ) -> None:
        self._page_view = page_view
        self._store = store
        self._schedule = schedule_autosave
        self._edit_mode = False

        page_view.page_will_change.connect(self._harvest_page)
        page_view.page_changed.connect(self._on_page_shown)
        page_view.delete_requested.connect(self.delete_selected)

    # --- public API ---------------------------------------------------------

    def reset_edit_mode(self) -> None:
        """Drop edit state on document load (mirrors the other controllers)."""
        self._edit_mode = False

    def set_edit_mode(self, on: bool) -> None:
        """Toggle whether the (always-visible) rectangles can be moved/resized."""
        if not on:
            self._harvest_page(self._page_view.current_page_index())
        self._edit_mode = on
        for item in self._page_view.rect_items():
            item.set_editable(on)

    def add_rect(
        self,
        width: float,
        height: float,
        color: str,
        anchor: QPointF | None = None,
        *,
        centered: bool = False,
    ) -> None:
        """Add a rectangle to the current page (edit mode only); placed on top."""
        if not self._edit_mode:
            return
        item = rect_style.build_item(width, height, color)
        place_new_item(
            self._page_view, item, anchor, centered=centered, add=self._page_view.add_rect_item
        )
        self._schedule()

    def delete_selected(self) -> None:
        """Remove the selected rectangles from the current page (edit mode only)."""
        if not self._edit_mode:
            return
        for item in self._page_view.rect_items():
            if item.isSelected():
                self._page_view.remove_rect_item(item)
        self._schedule()

    def set_selected_size(self, width: float, height: float) -> None:
        """Resize the selected rectangle to ``width`` x ``height``."""
        item = self._page_view.selected_rect_item()
        if item is not None:
            item.set_size(width, height)
            self._schedule()

    def notify_changed(self) -> None:
        """Schedule an autosave after an in-place edit (e.g. a fill-color change)."""
        self._schedule()

    def harvest_current(self) -> None:
        """Harvest live items on the current page back into the store."""
        self._harvest_page(self._page_view.current_page_index())

    def clear(self) -> None:
        """Remove the live rect items from the view (store cleared by the owner)."""
        self._page_view.clear_rect_items()

    # --- internals ----------------------------------------------------------

    def _harvest_page(self, index: int) -> None:
        self._store.set_rects(
            index,
            [rect_style.item_to_spec(item, index) for item in self._page_view.rect_items()],
        )

    def _on_page_shown(self, _current: int, _total: int) -> None:
        self._restore_page(self._page_view.current_page_index())

    def _restore_page(self, index: int) -> None:
        self._page_view.clear_rect_items()
        for spec in self._store.rects_on(index):
            item = rect_style.spec_to_item(spec)
            item.set_editable(self._edit_mode)
            self._page_view.add_rect_item(item)
            item.setZValue(spec.z)  # re-assert: ItemLayer.add forces the layer default
