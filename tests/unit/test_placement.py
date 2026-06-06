"""Unit tests for the text-field placement ordering policy (pure, no Qt)."""

from __future__ import annotations

import pytest

from app.gui.placement import PlacementMode, ordered_modes


def test_ordered_modes_puts_last_pick_first() -> None:
    ordered = ordered_modes(PlacementMode.VIEW_CENTER)
    assert ordered[0] is PlacementMode.VIEW_CENTER


@pytest.mark.parametrize("last", list(PlacementMode))
def test_ordered_modes_keeps_all_four_without_duplicates(last: PlacementMode) -> None:
    ordered = ordered_modes(last)
    assert ordered[0] is last
    assert set(ordered) == set(PlacementMode)
    assert len(ordered) == len(set(ordered)) == 4
