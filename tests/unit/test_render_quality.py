"""Unit tests for the pure render-quality decision logic (no Qt needed)."""

from __future__ import annotations

import pytest

from app.gui.render_quality import (
    MAX_QUALITY,
    needs_rerender,
    target_quality,
)


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
