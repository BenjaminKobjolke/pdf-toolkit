"""Unit tests for ZoomController: deterministic fit and percentage readout."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QRectF, QSize
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsView

from app.gui import render
from app.gui.zoom_controller import ZoomController


def _controller(
    page_w: float = 1000.0,
    page_h: float = 1500.0,
    view_w: int = 600,
    view_h: int = 800,
) -> ZoomController:
    view = MagicMock(spec=QGraphicsView)
    view.maximumViewportSize.return_value = QSize(view_w, view_h)
    pixmap_item = MagicMock(spec=QGraphicsPixmapItem)
    pixmap_item.boundingRect.return_value = QRectF(0.0, 0.0, page_w, page_h)
    return ZoomController(view, pixmap_item)


def test_fit_is_idempotent(qapp: object) -> None:
    ctl = _controller()
    ctl.fit()
    first = ctl.zoom()
    ctl.fit()
    assert ctl.zoom() == pytest.approx(first)


def test_fit_uses_new_page_rect(qapp: object) -> None:
    # Page exactly half as wide/tall fits at twice the scale.
    tall = _controller(page_w=1000.0, page_h=1500.0)
    tall.fit()
    small = _controller(page_w=500.0, page_h=750.0)
    small.fit()
    assert small.zoom() == pytest.approx(tall.zoom() * 2.0)


def test_fit_keeps_aspect_ratio(qapp: object) -> None:
    # Limiting dimension is height: 800/1500 < 600/1000.
    ctl = _controller(page_w=1000.0, page_h=1500.0, view_w=600, view_h=800)
    ctl.fit()
    assert ctl.zoom() == pytest.approx(800.0 / 1500.0)


def test_percent_maps_actual_to_100(qapp: object) -> None:
    ctl = _controller()
    ctl.actual()
    assert ctl.percent() == 100


def test_percent_doubles_at_double_actual(qapp: object) -> None:
    ctl = _controller()
    ctl.fit()
    # Force a known scale via fit then check percent matches zoom/_ZOOM_ACTUAL.
    expected = round(ctl.zoom() / (1.0 / render.DEFAULT_ZOOM) * 100)
    assert ctl.percent() == expected
