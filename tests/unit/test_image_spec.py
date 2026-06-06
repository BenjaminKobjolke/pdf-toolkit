"""Unit tests for the image/sidecar value objects."""

from __future__ import annotations

from app.pdf.image_spec import ImageFieldSpec, SidecarDocument
from app.pdf.text_spec import TextFieldSpec


def _image(page_index: int = 0) -> ImageFieldSpec:
    return ImageFieldSpec(page_index, 1.0, 2.0, 30.0, 40.0, "assets/x.png", absolute=False)


def _field() -> TextFieldSpec:
    return TextFieldSpec(0, 1.0, 2.0, 3.0, 4.0, "hi", "Helvetica", 18.0, "#000000", None)


def test_opacity_defaults_to_one() -> None:
    assert _image().opacity == 1.0


def test_images_on_page_filters() -> None:
    doc = SidecarDocument(images=(_image(0), _image(1), _image(1)))
    assert len(doc.images_on_page(1)) == 2
    assert doc.images_on_page(0) == (_image(0),)


def test_is_empty() -> None:
    assert SidecarDocument().is_empty()
    assert not SidecarDocument(fields=(_field(),)).is_empty()
    assert not SidecarDocument(images=(_image(),)).is_empty()
