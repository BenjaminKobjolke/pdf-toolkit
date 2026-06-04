"""Unit tests for PageView zoom, first/last navigation, and reset (offscreen Qt)."""

from __future__ import annotations

import pytest

from app.gui import render
from app.gui.page_view import PageView
from tests.conftest import MakePdf

_ACTUAL = 1.0 / render.DEFAULT_ZOOM


@pytest.fixture
def view(qapp: object, make_pdf: MakePdf) -> PageView:
    page_view = PageView()
    page_view.load(make_pdf([(200, 300), (200, 300), (200, 300)]))
    return page_view


def test_zoom_actual_sets_inverse_of_render_zoom(view: PageView) -> None:
    view.zoom_actual()
    assert view.zoom() == pytest.approx(_ACTUAL)


def test_zoom_in_multiplies(view: PageView) -> None:
    view.zoom_actual()
    view.zoom_in()
    assert view.zoom() == pytest.approx(_ACTUAL * 1.1)


def test_zoom_out_multiplies(view: PageView) -> None:
    view.zoom_actual()
    view.zoom_out()
    assert view.zoom() == pytest.approx(_ACTUAL * 0.9)


def test_zoom_applied_to_view_transform(view: PageView) -> None:
    view.zoom_actual()
    assert view.transform().m11() == pytest.approx(_ACTUAL)
    assert view.transform().m22() == pytest.approx(_ACTUAL)


def test_zoom_fit_sets_positive_scale(view: PageView) -> None:
    view.zoom_fit()
    assert view.zoom() > 0


def test_actual_zoom_persists_across_pages(view: PageView) -> None:
    view.zoom_actual()
    view.show_next()
    assert view.transform().m11() == pytest.approx(_ACTUAL)
    assert view.zoom() == pytest.approx(_ACTUAL)


def test_manual_zoom_persists_across_pages(view: PageView) -> None:
    view.zoom_actual()
    view.zoom_in()
    expected = _ACTUAL * 1.1
    view.show_next()
    assert view.transform().m11() == pytest.approx(expected)


def test_fit_mode_refits_each_page(view: PageView) -> None:
    view.zoom_fit()
    # Switching pages keeps fit mode (re-fits rather than reverting to a fixed
    # scale); the view stays in a fitted, positive-scale state.
    view.show_next()
    assert view.zoom() > 0


def test_show_last_then_first(view: PageView) -> None:
    view.show_last()
    assert view.current_page_one_based() == 3
    view.show_first()
    assert view.current_page_one_based() == 1


def test_show_first_last_no_doc_is_safe(qapp: object) -> None:
    empty = PageView()
    empty.show_first()
    empty.show_last()
    assert empty.total_pages() == 0


def test_reset_clears_document(view: PageView) -> None:
    view.reset()
    assert view.total_pages() == 0
    assert view.current_page_index() == 0
    assert view.source() is None
