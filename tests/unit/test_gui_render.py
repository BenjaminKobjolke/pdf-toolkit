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


def test_render_page_quality_tags_device_pixel_ratio(qapp: object, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(100, 200)])

    image = render.render_page(pdf, 0, quality=2.0)

    assert image.devicePixelRatio() == pytest.approx(2.0)


def test_render_page_quality_scales_physical_pixels(qapp: object, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(100, 200)])

    base = render.render_page(pdf, 0, quality=1.0)
    hi = render.render_page(pdf, 0, quality=3.0)

    assert hi.width() == base.width() * 3
    assert hi.height() == base.height() * 3


def test_render_page_quality_keeps_logical_size(qapp: object, make_pdf: MakePdf) -> None:
    """More physical pixels but the device-independent (scene) size is unchanged,
    so overlay coordinates never move when quality changes."""
    pdf = make_pdf([(100, 200)])

    base = render.render_page(pdf, 0, quality=1.0)
    hi = render.render_page(pdf, 0, quality=3.0)

    assert hi.width() / hi.devicePixelRatio() == pytest.approx(base.width())
    assert hi.height() / hi.devicePixelRatio() == pytest.approx(base.height())
