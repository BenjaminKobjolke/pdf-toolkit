"""A generic list of scene items at a fixed z-value.

Both placed text fields and placed images need the same bookkeeping: keep an
ordered list, add/remove/clear them on the scene, and report the current /
selected items. :class:`PageView` holds one layer per kind so the per-type
methods are not duplicated.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene

T = TypeVar("T", bound=QGraphicsItem)


class ItemLayer(Generic[T]):
    """An ordered set of scene items kept at one z-value."""

    def __init__(self, scene: QGraphicsScene, z_value: float) -> None:
        self._scene = scene
        self._z = z_value
        self._items: list[T] = []

    def add(self, item: T) -> None:
        item.setZValue(self._z)
        self._scene.addItem(item)
        self._items.append(item)

    def remove(self, item: T) -> None:
        if item in self._items:
            self._scene.removeItem(item)
            self._items.remove(item)

    def clear(self) -> None:
        for item in self._items:
            self._scene.removeItem(item)
        self._items.clear()

    def items(self) -> tuple[T, ...]:
        return tuple(self._items)

    def selected(self) -> T | None:
        """Return the first selected item, or ``None`` if none is selected."""
        for item in self._items:
            if item.isSelected():
                return item
        return None
