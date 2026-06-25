"""Shared selection/handle behaviour for resizable overlay items.

A mixin for the parts that :class:`~app.gui.image_item.ImageItem` and
:class:`~app.gui.rect_item.RectItem` share: toggling edit interaction, showing
corner handles only while selected, and drawing the configurable outline instead
of Qt's default marquee. Each item keeps its own ``_reposition_handles`` (the
corner geometry differs) and creates its own ``_handles`` list.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QGraphicsItem, QStyle, QStyleOptionGraphicsItem, QWidget

from app.gui import outline_style
from app.gui.gui_items import set_item_editable
from app.gui.image_resize import ResizeHandleItem


class ResizableItemMixin:
    """Editability + corner-handle visibility + custom selection outline."""

    _handles: list[ResizeHandleItem]
    _editable: bool

    def _reposition_handles(self) -> None:  # provided by the concrete item
        raise NotImplementedError

    def set_editable(self, on: bool) -> None:
        """Toggle move/resize interaction; the item stays visible either way."""
        self._editable = on
        set_item_editable(self, on)  # type: ignore[arg-type]
        self._set_handles_visible(on and self.isSelected())  # type: ignore[attr-defined]

    def itemChange(self, change: Any, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self._set_handles_visible(self._editable and bool(value))
        return super().itemChange(change, value)  # type: ignore[misc]

    def paint(
        self,
        painter: Any,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        # Suppress Qt's faint default selection marquee; draw our own outline.
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        option.state &= ~QStyle.StateFlag.State_Selected
        super().paint(painter, option, widget)  # type: ignore[misc]
        if selected:
            outline_style.active().draw(painter, self.boundingRect())  # type: ignore[attr-defined]

    def _set_handles_visible(self, visible: bool) -> None:
        for handle in self._handles:
            handle.setVisible(visible)
