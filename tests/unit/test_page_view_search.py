"""Unit tests for PageView absolute jump, highlights, and selection (offscreen Qt)."""

from __future__ import annotations

import pytest

from app.gui import render
from app.gui.page_view import PageView
from app.gui.text_item import TextFieldItem
from tests.conftest import MakePdf


@pytest.fixture
def view(qapp: object, make_pdf: MakePdf) -> PageView:
    page_view = PageView()
    page_view.load(make_pdf([(200, 300), (200, 300), (200, 300)]))
    return page_view


def test_go_to_page_jumps(view: PageView) -> None:
    view.go_to_page(2)
    assert view.current_page_one_based() == 3


def test_go_to_page_clamps(view: PageView) -> None:
    view.go_to_page(99)
    assert view.current_page_one_based() == 3
    view.go_to_page(-5)
    assert view.current_page_one_based() == 1


def test_set_highlights_scales_by_zoom(view: PageView) -> None:
    view.set_highlights([(10.0, 20.0, 30.0, 40.0)])
    assert view.has_highlights()
    item = view.highlight_items()[0]
    rect = item.rect()
    z = render.DEFAULT_ZOOM
    assert rect.x() == pytest.approx(10.0 * z)
    assert rect.y() == pytest.approx(20.0 * z)
    assert rect.right() == pytest.approx(30.0 * z)
    assert rect.bottom() == pytest.approx(40.0 * z)


def test_clear_highlights(view: PageView) -> None:
    view.set_highlights([(1.0, 2.0, 3.0, 4.0)])
    view.clear_highlights()
    assert not view.has_highlights()


def test_highlights_cleared_on_navigation(view: PageView) -> None:
    view.set_highlights([(1.0, 2.0, 3.0, 4.0)])
    view.go_to_page(1)
    assert not view.has_highlights()


def test_highlights_cleared_on_reset(view: PageView) -> None:
    view.set_highlights([(1.0, 2.0, 3.0, 4.0)])
    view.reset()
    assert not view.has_highlights()


def test_selected_text_item(view: PageView) -> None:
    assert view.selected_text_item() is None
    item = TextFieldItem("hi")
    item.set_editable(True)
    view.add_text_item(item)
    item.setSelected(True)
    assert view.selected_text_item() is item
