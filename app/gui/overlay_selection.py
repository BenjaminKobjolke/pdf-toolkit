"""Selection helpers spanning the text + image overlay layers.

Free functions (not methods) so :class:`~app.gui.page_view.PageView` stays under
the file-length cap and the page-input controller and window can share them. They
talk to the view through its public item accessors only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QGraphicsItem

if TYPE_CHECKING:
    from app.gui.page_view import PageView


def selected_movable_items(view: PageView) -> tuple[QGraphicsItem, ...]:
    """Return every selected overlay item (text + image) on the current page."""
    items: list[QGraphicsItem] = [it for it in view.text_items() if it.isSelected()]
    items.extend(it for it in view.image_items() if it.isSelected())
    return tuple(items)


def editable_items(view: PageView) -> tuple[QGraphicsItem, ...]:
    """Return the selectable overlay items in reading order (top-to-bottom, then left)."""
    items = [
        it
        for it in (*view.text_items(), *view.image_items())
        if it.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
    ]
    return tuple(sorted(items, key=lambda it: (it.pos().y(), it.pos().x())))


def select_adjacent_editable(view: PageView, forward: bool) -> bool:
    """Select the next / previous editable item, cycling. False if there are none."""
    items = editable_items(view)
    if not items:
        return False
    current = next((i for i, it in enumerate(items) if it.isSelected()), None)
    nxt = 0 if current is None else (current + (1 if forward else -1)) % len(items)
    view.graphics_scene().clearSelection()
    items[nxt].setSelected(True)
    items[nxt].ensureVisible()
    return True
