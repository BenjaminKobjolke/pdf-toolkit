"""MRU and cancel behaviour of the shared :func:`pick_color` helper.

The dialog itself is stubbed out — these tests pin the recent-colors contract:
front-insertion, dedupe, the cap, and that transparent/cancel never enter it.
"""

from __future__ import annotations

import pytest

from app.gui import color_picker_dialog
from app.gui.color_picker_dialog import pick_color


class _FakeDialog:
    """Stands in for ColorPickerDialog; returns a preset choice without Qt."""

    TRANSPARENT = color_picker_dialog.ColorPickerDialog.TRANSPARENT
    next_choice: str | None = None

    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs

    def exec(self) -> bool:
        return _FakeDialog.next_choice is not None

    def chosen(self) -> str | None:
        return _FakeDialog.next_choice


@pytest.fixture()
def fake_dialog(monkeypatch: pytest.MonkeyPatch) -> type[_FakeDialog]:
    monkeypatch.setattr(color_picker_dialog, "ColorPickerDialog", _FakeDialog)
    return _FakeDialog


def _pick(choice: str | None, recent: list[str]) -> str | None:
    _FakeDialog.next_choice = choice
    return pick_color(None, recent)


def test_picked_color_lands_at_front(fake_dialog: type[_FakeDialog]) -> None:
    recent = ["#111111"]
    assert _pick("#222222", recent) == "#222222"
    assert recent == ["#222222", "#111111"]


def test_repeat_pick_moves_to_front_without_duplicate(fake_dialog: type[_FakeDialog]) -> None:
    recent = ["#111111", "#222222"]
    assert _pick("#222222", recent) == "#222222"
    assert recent == ["#222222", "#111111"]


def test_recent_list_is_capped_at_eight(fake_dialog: type[_FakeDialog]) -> None:
    recent: list[str] = []
    for i in range(9):
        _pick(f"#{i:06x}", recent)
    assert len(recent) == 8
    assert "#000000" not in recent  # oldest pick dropped
    assert recent[0] == "#000008"


def test_cancel_returns_none_and_keeps_recent(fake_dialog: type[_FakeDialog]) -> None:
    recent = ["#111111"]
    assert _pick(None, recent) is None
    assert recent == ["#111111"]


def test_transparent_is_returned_but_not_remembered(fake_dialog: type[_FakeDialog]) -> None:
    recent: list[str] = []
    _FakeDialog.next_choice = _FakeDialog.TRANSPARENT
    assert pick_color(None, recent, allow_transparent=True) == _FakeDialog.TRANSPARENT
    assert recent == []
