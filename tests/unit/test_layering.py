"""Unit tests for the pure stacking-order maths in ``app.gui.layering``."""

from __future__ import annotations

from dataclasses import dataclass

from app.gui import layering


@dataclass
class _Fake:
    name: str
    z: float

    def get_z(self) -> float:
        return self.z

    def set_z(self, value: float) -> None:
        self.z = value


def _order(items: list[_Fake]) -> list[str]:
    return [it.name for it in sorted(items, key=lambda it: it.z)]


def _items() -> list[_Fake]:
    return [_Fake("a", 0.0), _Fake("b", 1.0), _Fake("c", 2.0)]


def test_bring_to_front_moves_to_top() -> None:
    items = _items()
    layering.bring_to_front(items[0], items)  # a
    assert _order(items) == ["b", "c", "a"]


def test_send_to_back_moves_to_bottom() -> None:
    items = _items()
    layering.send_to_back(items[2], items)  # c
    assert _order(items) == ["c", "a", "b"]


def test_move_forward_swaps_with_next_above() -> None:
    items = _items()
    layering.move_forward(items[0], items)  # a: a,b,c -> b,a,c
    assert _order(items) == ["b", "a", "c"]


def test_move_backward_swaps_with_next_below() -> None:
    items = _items()
    layering.move_backward(items[2], items)  # c: a,b,c -> a,c,b
    assert _order(items) == ["a", "c", "b"]


def test_move_forward_at_top_is_noop() -> None:
    items = _items()
    layering.move_forward(items[2], items)  # c already top
    assert _order(items) == ["a", "b", "c"]


def test_move_backward_at_bottom_is_noop() -> None:
    items = _items()
    layering.move_backward(items[0], items)  # a already bottom
    assert _order(items) == ["a", "b", "c"]


def test_normalize_makes_dense_integer_order() -> None:
    items = [_Fake("a", 5.0), _Fake("b", -3.0), _Fake("c", 100.0)]
    layering.normalize(items)
    assert sorted(it.z for it in items) == [0.0, 1.0, 2.0]
    assert _order(items) == ["b", "a", "c"]


def test_ops_keep_order_dense_after_repeated_moves() -> None:
    items = _items()
    for _ in range(5):
        layering.move_forward(items[0], items)
        layering.send_to_back(items[0], items)
    assert sorted(it.z for it in items) == [0.0, 1.0, 2.0]
