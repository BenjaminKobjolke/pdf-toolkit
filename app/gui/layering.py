"""Pure stacking-order maths for overlay elements (text, image, rect).

Qt-free on purpose: it works on anything exposing ``get_z`` / ``set_z`` (a thin
adapter wraps a live ``QGraphicsItem`` at the call site), so the reorder logic is
unit-testable without a display. Higher ``z`` paints in front. After every op the
caller-facing helpers re-``normalize`` to a dense ``0..n-1`` integer order so the
values never drift apart over many moves.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol


class Layerable(Protocol):
    """Anything carrying a mutable stacking value."""

    def get_z(self) -> float: ...

    def set_z(self, value: float) -> None: ...


def _ordered(items: Sequence[Layerable]) -> list[Layerable]:
    """Return ``items`` back-to-front (ascending z); stable on ties."""
    return sorted(items, key=lambda it: it.get_z())


def normalize(items: Sequence[Layerable]) -> None:
    """Reassign a dense ``0, 1, 2 …`` order matching the current z ranking."""
    for index, item in enumerate(_ordered(items)):
        item.set_z(float(index))


def bring_to_front(item: Layerable, items: Sequence[Layerable]) -> None:
    """Move ``item`` above every other element."""
    item.set_z(_max_z(items) + 1.0)
    normalize(items)


def send_to_back(item: Layerable, items: Sequence[Layerable]) -> None:
    """Move ``item`` below every other element."""
    item.set_z(_min_z(items) - 1.0)
    normalize(items)


def move_forward(item: Layerable, items: Sequence[Layerable]) -> None:
    """Swap ``item`` with the next element above it (no-op if already top)."""
    _swap_with_neighbor(item, items, ahead=True)


def move_backward(item: Layerable, items: Sequence[Layerable]) -> None:
    """Swap ``item`` with the next element below it (no-op if already bottom)."""
    _swap_with_neighbor(item, items, ahead=False)


def _swap_with_neighbor(item: Layerable, items: Sequence[Layerable], *, ahead: bool) -> None:
    order = _ordered(items)
    if item not in order:
        return
    pos = order.index(item)
    neighbor = pos + 1 if ahead else pos - 1
    if not 0 <= neighbor < len(order):
        return
    other = order[neighbor]
    item_z, other_z = item.get_z(), other.get_z()
    item.set_z(other_z)
    other.set_z(item_z)
    normalize(items)


def _max_z(items: Sequence[Layerable]) -> float:
    return max((it.get_z() for it in items), default=0.0)


def _min_z(items: Sequence[Layerable]) -> float:
    return min((it.get_z() for it in items), default=0.0)
