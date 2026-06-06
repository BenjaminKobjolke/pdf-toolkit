"""Unit tests for the placement creator-callback generalization (offscreen Qt)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPointF

from app.config.placement_settings import PlacementStore
from app.gui.mode_status_bar import ModeStatusBar
from app.gui.page_view import PageView
from app.gui.placement import PlacementController, PlacementMode


def _controller(tmp_path: Path) -> PlacementController:
    return PlacementController(
        None,  # parent unused for the non-dialog paths exercised here
        PageView(),
        ModeStatusBar(),
        PlacementStore(tmp_path / "placement.json"),
    )


def test_top_left_invokes_creator_with_no_anchor(
    qapp: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pc = _controller(tmp_path)
    monkeypatch.setattr(pc, "_choose", lambda: PlacementMode.TOP_LEFT)
    calls: list[tuple[QPointF | None, bool]] = []
    pc.choose_and_place(lambda anchor, centered: calls.append((anchor, centered)))
    assert calls == [(None, False)]


def test_page_center_invokes_creator_centered(
    qapp: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pc = _controller(tmp_path)
    monkeypatch.setattr(pc, "_choose", lambda: PlacementMode.PAGE_CENTER)
    calls: list[tuple[QPointF | None, bool]] = []
    pc.choose_and_place(lambda anchor, centered: calls.append((anchor, centered)))
    assert len(calls) == 1
    anchor, centered = calls[0]
    assert isinstance(anchor, QPointF)
    assert centered is True
