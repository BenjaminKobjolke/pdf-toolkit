"""ZoomController.set_default: percent maps to a scaled factor, fit picks fit mode."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsView

from app.gui.zoom_controller import _MODE_FIT, _MODE_SCALED, _ZOOM_ACTUAL, ZoomController


def _controller(qapp: object) -> ZoomController:
    view = QGraphicsView()
    return ZoomController(view, QGraphicsPixmapItem())


def test_set_default_percent_sets_scaled_factor(qapp: object) -> None:
    ctl = _controller(qapp)
    ctl.set_default(fit=False, percent=50)
    assert ctl._mode == _MODE_SCALED
    assert ctl.zoom() == pytest.approx(0.5 * _ZOOM_ACTUAL)


def test_set_default_fit_sets_fit_mode(qapp: object) -> None:
    ctl = _controller(qapp)
    ctl.set_default(fit=True, percent=100)
    assert ctl._mode == _MODE_FIT
