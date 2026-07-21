"""Unit tests for app.gui.render (offscreen Qt)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from PIL import Image
from PySide6.QtGui import QColor, QImage

from app.config.image_background_settings import ImageBackground, ImageBackgroundSettings
from app.gui import render
from tests.conftest import MakeImage, MakePdf


@pytest.fixture(autouse=True)
def _reset_image_background() -> Iterator[None]:
    """Keep the module-level active backdrop from leaking between tests."""
    yield
    render.set_image_background(ImageBackgroundSettings())


def test_page_count_matches_pdf(make_pdf: MakePdf) -> None:
    pdf = make_pdf([(100, 200), (300, 400), (120, 120)])

    assert render.page_count(pdf) == 3


def test_page_size_returns_point_dimensions(make_pdf: MakePdf) -> None:
    pdf = make_pdf([(100, 200), (300, 400)])

    assert render.page_size(pdf, 0) == pytest.approx((100.0, 200.0))
    assert render.page_size(pdf, 1) == pytest.approx((300.0, 400.0))


def test_doc_metadata_empty_when_absent(make_pdf: MakePdf) -> None:
    pdf = make_pdf([(100, 200)])

    meta = render.doc_metadata(pdf)

    assert meta.title == ""
    assert meta.author == ""


def test_render_page_returns_nonempty_image(qapp: object, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(100, 200), (300, 400)])

    image = render.render_page(pdf, 0)

    assert not image.isNull()
    assert image.width() > 0
    assert image.height() > 0


def test_render_page_renders_psd(qapp: object, make_image: MakeImage) -> None:
    psd = make_image("psd")

    assert render.page_count(psd) == 1
    image = render.render_page(psd, 0)
    assert not image.isNull()
    assert image.width() > 0


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


# --- transparency backdrop (compose + render seam) ---------------------------


def _transparent_image(size: int) -> QImage:
    image = QImage(size, size, QImage.Format.Format_RGBA8888)
    image.fill(QColor(0, 0, 0, 0))
    return image


def _transparent_png(tmp_path: Path, size: int = 16) -> Path:
    target = tmp_path / "transparent.png"
    Image.new("RGBA", (size, size), (0, 0, 0, 0)).save(target)
    return target


@pytest.mark.parametrize(
    ("background", "expected"),
    [
        (ImageBackground.WHITE, "#ffffff"),
        (ImageBackground.BLACK, "#000000"),
        (ImageBackground.GREEN, "#00ff00"),
        (ImageBackground.BLUE, "#0000ff"),
    ],
)
def test_compose_solid_fills_transparent_pixels(
    qapp: object, background: ImageBackground, expected: str
) -> None:
    result = render.compose(_transparent_image(4), background)

    assert QColor(result.pixel(0, 0)).name() == expected
    assert QColor(result.pixel(3, 3)).name() == expected


def test_compose_keeps_opaque_pixels(qapp: object) -> None:
    image = _transparent_image(4)
    image.setPixelColor(1, 1, QColor(10, 20, 30, 255))

    result = render.compose(image, ImageBackground.BLACK)

    assert QColor(result.pixel(1, 1)).name() == "#0a141e"


def test_compose_checker_pattern(qapp: object) -> None:
    result = render.compose(_transparent_image(16), ImageBackground.CHECKER)

    assert QColor(result.pixel(0, 0)).name() == "#ffffff"
    assert QColor(result.pixel(8, 0)).name() == "#cccccc"
    assert QColor(result.pixel(0, 8)).name() == "#cccccc"
    assert QColor(result.pixel(8, 8)).name() == "#ffffff"


def test_compose_preserves_device_pixel_ratio(qapp: object) -> None:
    image = _transparent_image(4)
    image.setDevicePixelRatio(2.0)

    result = render.compose(image, ImageBackground.WHITE)

    assert result.devicePixelRatio() == pytest.approx(2.0)


def test_active_image_background_defaults_to_white() -> None:
    assert render.active_image_background() is ImageBackground.WHITE


def test_set_image_background_round_trip() -> None:
    render.set_image_background(ImageBackgroundSettings(background=ImageBackground.CHECKER))
    assert render.active_image_background() is ImageBackground.CHECKER


def test_render_page_applies_active_background_to_images(qapp: object, tmp_path: Path) -> None:
    png = _transparent_png(tmp_path)
    render.set_image_background(ImageBackgroundSettings(background=ImageBackground.GREEN))

    image = render.render_page(png, 0)

    assert QColor(image.pixel(0, 0)).name() == "#00ff00"


def test_render_page_defaults_keep_white_status_quo(qapp: object, tmp_path: Path) -> None:
    png = _transparent_png(tmp_path)

    image = render.render_page(png, 0)

    assert QColor(image.pixel(0, 0)).name() == "#ffffff"


def test_render_page_background_never_touches_pdfs(qapp: object, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(50, 50)])
    render.set_image_background(ImageBackgroundSettings(background=ImageBackground.CHECKER))

    image = render.render_page(pdf, 0)

    assert QColor(image.pixel(10, 10)).name() == "#ffffff"
