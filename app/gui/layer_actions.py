"""Stacking-order commands for the selected overlay element (any kind).

Wraps each live ``QGraphicsItem`` in a tiny ``get_z`` / ``set_z`` adapter and
defers the actual reorder to the Qt-free maths in :mod:`app.gui.layering`, then
schedules an autosave so the new order persists. Operates across every overlay
kind (text, image, rect) so a single z-order spans them all.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QGraphicsItem

from app.gui import layering
from app.gui.edit_controller import EditController
from app.gui.layering import Layerable
from app.gui.overlay_selection import all_overlay_items, selected_overlay_item
from app.gui.page_view import PageView


class _ZAdapter:
    """Exposes a scene item's z-value through the ``Layerable`` protocol."""

    def __init__(self, item: QGraphicsItem) -> None:
        self.item = item

    def get_z(self) -> float:
        return self.item.zValue()

    def set_z(self, value: float) -> None:
        self.item.setZValue(value)


Op = Callable[[Layerable, list[Layerable]], None]


class LayerActions:
    """Move the selected element forward/backward or to the front/back."""

    def __init__(self, page_view: PageView, controller: EditController) -> None:
        self._page_view = page_view
        self._controller = controller

    def has_selection(self) -> bool:
        """Whether one overlay element is selected (gates the layering commands)."""
        return selected_overlay_item(self._page_view) is not None

    def move_forward(self) -> None:
        self._apply(layering.move_forward)

    def move_backward(self) -> None:
        self._apply(layering.move_backward)

    def bring_to_front(self) -> None:
        self._apply(layering.bring_to_front)

    def send_to_back(self) -> None:
        self._apply(layering.send_to_back)

    def _apply(self, op: Op) -> None:
        target = selected_overlay_item(self._page_view)
        if target is None:
            return
        adapters = [_ZAdapter(it) for it in all_overlay_items(self._page_view)]
        wrapped: list[Layerable] = list(adapters)
        current = next(a for a in adapters if a.item is target)
        op(current, wrapped)
        self._controller.schedule_autosave()
