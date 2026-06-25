"""Selection helpers spanning the text + image overlay layers.

Free functions (not methods) so :class:`~app.gui.page_view.PageView` stays under
the file-length cap and the page-input controller and window can share them. They
talk to the view through its public item accessors only.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar

from PySide6.QtWidgets import QGraphicsItem

if TYPE_CHECKING:
    from PySide6.QtCore import QPointF

    from app.gui.page_view import PageView

_NEW_ITEM_POS = (40.0, 40.0)  # default top-left for a newly added overlay item
_Item = TypeVar("_Item", bound=QGraphicsItem)


def all_overlay_items(view: PageView) -> tuple[QGraphicsItem, ...]:
    """Return every overlay item (text + image + rect) on the current page."""
    return (*view.text_items(), *view.image_items(), *view.rect_items())


def selected_movable_items(view: PageView) -> tuple[QGraphicsItem, ...]:
    """Return every selected overlay item (text + image + rect) on the current page."""
    return tuple(it for it in all_overlay_items(view) if it.isSelected())


def selected_overlay_item(view: PageView) -> QGraphicsItem | None:
    """Return the single selected overlay item of any kind, or ``None``."""
    selected = selected_movable_items(view)
    return selected[0] if selected else None


def next_front_z(view: PageView) -> float:
    """Return a z value above every current overlay item (so a new item is on top)."""
    items = all_overlay_items(view)
    return max((it.zValue() for it in items), default=0.0) + 1.0


def place_new_item(
    view: PageView,
    item: _Item,
    anchor: QPointF | None,
    *,
    centered: bool,
    add: Callable[[_Item], None],
) -> None:
    """Position a freshly created overlay ``item``, add it on top, and select it.

    ``anchor`` (scene px): ``None`` = top-left default; else placed at — or centred
    on, when ``centered`` — ``anchor``. ``add`` is the view's per-kind add method
    (``add_text_item`` etc.). The caller schedules the autosave afterwards.
    """
    if anchor is None:
        item.setPos(*_NEW_ITEM_POS)
    elif centered:
        center = item.boundingRect().center()
        item.setPos(anchor.x() - center.x(), anchor.y() - center.y())
    else:
        item.setPos(anchor)
    front = next_front_z(view)
    add(item)
    item.setZValue(front)  # new items land on top of existing overlay items
    view.graphics_scene().clearSelection()
    item.setSelected(True)  # active target right after creation


def editable_items(view: PageView) -> tuple[QGraphicsItem, ...]:
    """Return the selectable overlay items in reading order (top-to-bottom, then left)."""
    items = [
        it
        for it in all_overlay_items(view)
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
