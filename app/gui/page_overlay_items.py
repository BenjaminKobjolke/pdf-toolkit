"""Per-kind overlay accessors for :class:`~app.gui.page_view.PageView`.

A mixin holding the thin wrappers for each overlay: the three item layers
(text, image, rect) plus the search-highlight and text-selection overlays.
Split out so ``page_view`` stays under the file-length cap; the layers
themselves are created in ``PageView.__init__``.
"""

from __future__ import annotations

from PySide6.QtWidgets import QGraphicsRectItem

from app.gui.image_item import ImageItem
from app.gui.item_layer import ItemLayer
from app.gui.page_highlights import PageHighlights
from app.gui.rect_item import RectItem
from app.gui.selection_highlights import SelectionHighlights
from app.gui.text_item import TextFieldItem


class OverlayItemsMixin:
    """Add/query/remove helpers for the item layers and highlight overlays."""

    _text_layer: ItemLayer[TextFieldItem]
    _image_layer: ItemLayer[ImageItem]
    _rect_layer: ItemLayer[RectItem]
    _highlights: PageHighlights
    _selection: SelectionHighlights

    # --- search highlights ---------------------------------------------------

    def set_highlights(self, rects_pts: list[tuple[float, float, float, float]]) -> None:
        """Draw gold outlines for the given match rects (in PDF points)."""
        self._highlights.set(rects_pts)

    def clear_highlights(self) -> None:
        self._highlights.clear()

    def has_highlights(self) -> bool:
        return self._highlights.has()

    def highlight_items(self) -> tuple[QGraphicsRectItem, ...]:
        return self._highlights.items()

    def highlight_rects_points(self) -> list[tuple[float, float, float, float]]:
        """Return the current search-match rects in PDF points (empty when none)."""
        return self._highlights.rects_points()

    # --- text-selection overlay (vim-style select mode) ----------------------

    def selection_highlights(self) -> SelectionHighlights:
        """Expose the select-mode overlay so the controller can draw on it."""
        return self._selection

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

    # --- rect items ---------------------------------------------------------

    def add_rect_item(self, item: RectItem) -> None:
        self._rect_layer.add(item)

    def rect_items(self) -> tuple[RectItem, ...]:
        return self._rect_layer.items()

    def selected_rect_item(self) -> RectItem | None:
        """Return the first selected rectangle on the current page, if any."""
        return self._rect_layer.selected()

    def remove_rect_item(self, item: RectItem) -> None:
        self._rect_layer.remove(item)

    def clear_rect_items(self) -> None:
        self._rect_layer.clear()
