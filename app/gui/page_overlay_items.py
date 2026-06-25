"""Per-kind overlay item accessors for :class:`~app.gui.page_view.PageView`.

A mixin holding the thin add/items/selected/remove/clear wrappers for each of the
three overlay layers (text, image, rect). Split out so ``page_view`` stays under
the file-length cap; the layers themselves are created in ``PageView.__init__``.
"""

from __future__ import annotations

from app.gui.image_item import ImageItem
from app.gui.item_layer import ItemLayer
from app.gui.rect_item import RectItem
from app.gui.text_item import TextFieldItem


class OverlayItemsMixin:
    """Add/query/remove helpers for the text, image, and rect layers."""

    _text_layer: ItemLayer[TextFieldItem]
    _image_layer: ItemLayer[ImageItem]
    _rect_layer: ItemLayer[RectItem]

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
