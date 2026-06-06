"""Integration: re-rendering at a higher quality keeps the scene + overlays put.

The blur fix raises pixel density via the image device-pixel-ratio while holding
the pixmap's logical (scene) size constant, so text fields and search highlights
must not move when a page is re-rendered sharper. A zoom change must also
schedule a coalesced re-render.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QPointF

from app.gui.page_view import PageView
from app.gui.text_item import TextFieldItem
from tests.conftest import MakePdf


@pytest.fixture
def view(qapp: object, make_pdf: MakePdf) -> PageView:
    page_view = PageView()
    page_view.load(make_pdf([(200, 300)]))
    return page_view


def test_rerender_at_higher_quality_keeps_scene_and_overlay(view: PageView) -> None:
    item = TextFieldItem("hi")
    view.add_text_item(item)
    item.setPos(QPointF(40.0, 60.0))

    view._render_ctl.render_at(1.0)
    base_w = view._pixmap_item.pixmap().width()
    base_rect = view.graphics_scene().sceneRect()

    view._render_ctl.render_at(3.0)

    # 3x the physical pixels...
    assert view._pixmap_item.pixmap().width() == base_w * 3
    # ...but the logical scene size and the overlay position are unchanged.
    assert view._pixmap_item.boundingRect().width() == pytest.approx(base_rect.width())
    assert item.pos() == QPointF(40.0, 60.0)


def test_zoom_in_schedules_a_rerender(view: PageView) -> None:
    # Land at a known quality first so the small per-step change is measured
    # against it; then zoom in enough to cross the re-render threshold.
    view._render_ctl.render_at(1.0)
    for _ in range(5):
        view.zoom_in()

    assert view._render_ctl._timer.isActive()
