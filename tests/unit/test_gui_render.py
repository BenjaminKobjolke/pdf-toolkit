"""Unit tests for app.gui.render (offscreen Qt)."""

from __future__ import annotations

import pytest

from app.gui import render
from tests.conftest import MakePdf


def test_page_count_matches_pdf(make_pdf: MakePdf) -> None:
    pdf = make_pdf([(100, 200), (300, 400), (120, 120)])

    assert render.page_count(pdf) == 3


def test_render_page_returns_nonempty_image(qapp: object, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(100, 200), (300, 400)])

    image = render.render_page(pdf, 0)

    assert not image.isNull()
    assert image.width() > 0
    assert image.height() > 0


def test_render_page_rejects_out_of_range(qapp: object, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(100, 200)])

    with pytest.raises(ValueError, match="out of range"):
        render.render_page(pdf, 5)
