"""Unit tests for the pure render-quality decision logic (no Qt needed)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QGraphicsPixmapItem

from app.gui import render
from app.gui.render_quality import (
    MAX_QUALITY,
    RenderQualityController,
    needs_rerender,
    target_quality,
)


class _RenderView(QObject):
    def __init__(self, source: Path | None) -> None:
        super().__init__()
        self._source = source

    def source(self) -> Path | None:
        return self._source

    def current_page_index(self) -> int:
        return 0

    def zoom(self) -> float:
        return 1.0

    def devicePixelRatioF(self) -> float:
        return 1.0


def test_target_quality_is_scale_times_dpr() -> None:
    assert target_quality(1.0, 1.5) == pytest.approx(1.5)
    assert target_quality(2.0, 2.0) == pytest.approx(4.0)


def test_target_quality_caps_at_max() -> None:
    assert target_quality(100.0, 2.0) == pytest.approx(MAX_QUALITY)


def test_target_quality_has_floor() -> None:
    assert target_quality(0.0, 1.0) > 0.0


def test_needs_rerender_ignores_small_changes() -> None:
    # within +/-15% of the loaded quality -> not worth re-rendering
    assert needs_rerender(1.0, 1.1) is False


def test_needs_rerender_triggers_on_large_changes() -> None:
    assert needs_rerender(1.0, 1.5) is True


def test_needs_rerender_when_nothing_loaded() -> None:
    assert needs_rerender(0.0, 1.0) is True


def test_render_at_skips_deleted_source(
    qapp: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    missing = tmp_path / "deleted.pdf"
    controller = RenderQualityController(_RenderView(missing), QGraphicsPixmapItem())  # type: ignore[arg-type]

    def fail_render_page(source: Path, page_index: int, quality: float) -> object:
        raise AssertionError("render_page should not run for a missing source")

    monkeypatch.setattr(render, "render_page", fail_render_page)

    assert controller.render_at(1.0) is False
