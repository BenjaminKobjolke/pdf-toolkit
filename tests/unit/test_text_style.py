"""Unit tests for QColor<->hex and item<->spec mapping (offscreen Qt)."""

from __future__ import annotations

from app.gui import text_style
from app.gui.text_style import color_to_hex, hex_to_color, item_to_spec, spec_to_item
from app.pdf.text_spec import TextFieldSpec


def test_color_hex_round_trip(qapp: object) -> None:
    assert color_to_hex(hex_to_color("#ff8800")) == "#ff8800"


def test_spec_item_round_trip(qapp: object) -> None:
    spec = TextFieldSpec(
        page_index=0,
        x=30.0,
        y=40.0,
        width=0.0,
        height=0.0,
        text="Round trip",
        font_family="Helvetica",
        font_size=24.0,
        color="#112233",
        bg_color="#445566",
        bold=True,
        italic=True,
    )
    item = spec_to_item(spec)
    out = item_to_spec(item, page_index=0)

    assert out.text == spec.text
    assert out.x == spec.x and out.y == spec.y
    assert out.font_size == spec.font_size
    assert out.color == spec.color
    assert out.bg_color == spec.bg_color
    assert out.bold and out.italic


def test_transparent_bg_stays_none(qapp: object) -> None:
    spec = _spec(bg_color=None)
    item = spec_to_item(spec)
    assert item.bg_color() is None
    assert item_to_spec(item, 0).bg_color is None


def test_default_style_is_transparent() -> None:
    assert text_style.DEFAULT_STYLE.bg_color is None


def _spec(**overrides: object) -> TextFieldSpec:
    base: dict[str, object] = {
        "page_index": 0,
        "x": 1.0,
        "y": 2.0,
        "width": 0.0,
        "height": 0.0,
        "text": "x",
        "font_family": "Helvetica",
        "font_size": 18.0,
        "color": "#000000",
        "bg_color": None,
        "bold": False,
        "italic": False,
    }
    base.update(overrides)
    return TextFieldSpec(**base)  # type: ignore[arg-type]
