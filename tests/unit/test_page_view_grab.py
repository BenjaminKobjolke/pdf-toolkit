"""Unit test for PageView.grab_page_area — view grab clipped to the page (offscreen Qt)."""

from __future__ import annotations

from app.gui.page_view import PageView
from tests.conftest import MakePdf


def test_grab_page_area_clips_to_visible_page(qapp: object, make_pdf: MakePdf) -> None:
    view = PageView()
    view.load(make_pdf([(200, 300)]))
    view.resize(800, 600)
    view.zoom_actual()

    rect = view.visible_page_rect()
    viewport = view.viewport()
    assert not rect.isEmpty()
    assert rect.width() < viewport.width()

    pixmap = view.grab_page_area()
    dpr = pixmap.devicePixelRatio()
    assert pixmap.width() == round(rect.width() * dpr)
    assert pixmap.height() == round(rect.height() * dpr)

    # Without a document the page rect is empty — fall back to the full viewport grab.
    empty_view = PageView()
    assert empty_view.visible_page_rect().isEmpty()
    fallback = empty_view.grab_page_area()
    assert fallback.size() == empty_view.viewport().grab().size()
