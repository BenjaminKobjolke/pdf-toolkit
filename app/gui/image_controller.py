"""Owns the image side of the editing model: per-page items, harvest/restore.

Parallel to the text path in :class:`EditController`, but it does NOT persist:
the shared :class:`PageItemStore` and the single autosave timer live in
``EditController``, which writes both kinds in one save. This controller only
manages the live image items on the page and keeps the store's image dict in
sync on navigation, add, delete, and scale.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QPointF

from app.gui import image_style
from app.gui.overlay_selection import place_new_item
from app.gui.page_item_store import PageItemStore
from app.gui.page_view import PageView


class ImageController:
    """Coordinates placed images between the page view and the shared store."""

    def __init__(
        self, page_view: PageView, store: PageItemStore, schedule_autosave: Callable[[], None]
    ) -> None:
        self._page_view = page_view
        self._store = store
        self._schedule = schedule_autosave
        self._edit_mode = False
        self._base_dir: Path | None = None

        page_view.page_will_change.connect(self._harvest_page)
        page_view.page_changed.connect(self._on_page_shown)
        page_view.delete_requested.connect(self.delete_selected)

    # --- public API ---------------------------------------------------------

    def set_base_dir(self, base_dir: Path) -> None:
        """Set the directory that relative (assets) image paths resolve against."""
        self._base_dir = base_dir

    def reset_edit_mode(self) -> None:
        """Drop edit state on document load (mirrors the text controller)."""
        self._edit_mode = False

    def set_edit_mode(self, on: bool) -> None:
        """Toggle whether the (always-visible) images can be moved/scaled."""
        if not on:
            self._harvest_page(self._page_view.current_page_index())
        self._edit_mode = on
        for item in self._page_view.image_items():
            item.set_editable(on)

    def add_image(
        self,
        load_from: Path,
        path_str: str,
        absolute: bool,
        anchor: QPointF | None = None,
        *,
        centered: bool = False,
    ) -> None:
        """Add an image (loaded from ``load_from``) to the current page (edit mode only)."""
        if not self._edit_mode or self._base_dir is None:
            return
        item = image_style.build_item(load_from, path_str, absolute)
        place_new_item(
            self._page_view, item, anchor, centered=centered, add=self._page_view.add_image_item
        )
        self._schedule()

    def delete_selected(self) -> None:
        """Remove the selected images from the current page (edit mode only)."""
        if not self._edit_mode:
            return
        for item in self._page_view.image_items():
            if item.isSelected():
                self._page_view.remove_image_item(item)
        self._schedule()

    def selected_scale(self) -> float | None:
        """Return the selected image's scale factor, or ``None`` if none selected."""
        item = self._page_view.selected_image_item()
        return item.scale_factor() if item is not None else None

    def set_selected_scale(self, factor: float) -> None:
        """Set the selected image's uniform scale factor."""
        item = self._page_view.selected_image_item()
        if item is not None:
            item.scale_about_center(factor)
            self._schedule()

    def harvest_current(self) -> None:
        """Harvest live items on the current page back into the store."""
        self._harvest_page(self._page_view.current_page_index())

    def clear(self) -> None:
        """Remove the live image items from the view (store cleared by the owner)."""
        self._page_view.clear_image_items()

    # --- internals ----------------------------------------------------------

    def _harvest_page(self, index: int) -> None:
        self._store.set_images(
            index,
            [image_style.item_to_spec(item, index) for item in self._page_view.image_items()],
        )

    def _on_page_shown(self, _current: int, _total: int) -> None:
        self._restore_page(self._page_view.current_page_index())

    def _restore_page(self, index: int) -> None:
        self._page_view.clear_image_items()
        if self._base_dir is None:
            return
        for spec in self._store.images_on(index):
            item = image_style.spec_to_item(spec, self._base_dir)
            item.set_editable(self._edit_mode)
            self._page_view.add_image_item(item)
            item.setZValue(spec.z)  # re-assert: ItemLayer.add forces the layer default
