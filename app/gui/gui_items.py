"""Small shared helpers for scene items (text fields and images).

Keeps the editability flag-toggling in one place so :class:`TextFieldItem` and
:class:`ImageItem` cannot drift apart.
"""

from __future__ import annotations

from PySide6.QtWidgets import QGraphicsItem


def set_item_editable(item: QGraphicsItem, on: bool) -> None:
    """Toggle move/select interaction for ``item``; it stays visible either way.

    Deselects when turning editing off so a read-only item never keeps a stale
    selection.
    """
    item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, on)
    item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, on)
    if not on:
        item.setSelected(False)
