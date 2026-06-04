"""Style value object plus the Qt <-> spec mapping for text fields.

Keeps QColor/QFont conversions out of both the pure DTOs (``text_spec``) and the
view widgets, so the controller can move cleanly between live items and specs.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtGui import QColor

from app.gui.text_item import TextFieldItem
from app.pdf.text_spec import TextFieldSpec


@dataclass(frozen=True)
class TextStyle:
    """The styling the edit bar applies to the selected / next text field."""

    font_family: str
    font_size: float  # scene px
    color: str  # "#rrggbb"
    bg_color: str | None  # "#rrggbb" or None (transparent)
    bold: bool
    italic: bool


DEFAULT_STYLE = TextStyle(
    font_family="Helvetica",
    font_size=18.0,
    color="#000000",
    bg_color=None,
    bold=False,
    italic=False,
)


def color_to_hex(color: QColor) -> str:
    return color.name(QColor.NameFormat.HexRgb)


def hex_to_color(value: str) -> QColor:
    return QColor(value)


def apply_style(item: TextFieldItem, style: TextStyle) -> None:
    item.set_font_family(style.font_family)
    item.set_font_pixel_size(style.font_size)
    item.set_bold(style.bold)
    item.set_italic(style.italic)
    item.set_text_color(hex_to_color(style.color))
    item.set_bg_color(hex_to_color(style.bg_color) if style.bg_color is not None else None)


def item_to_style(item: TextFieldItem) -> TextStyle:
    """Read the styling of a live item back into a :class:`TextStyle`."""
    bg = item.bg_color()
    return TextStyle(
        font_family=item.font_family(),
        font_size=item.font_pixel_size(),
        color=color_to_hex(item.text_color()),
        bg_color=color_to_hex(bg) if bg is not None else None,
        bold=item.is_bold(),
        italic=item.is_italic(),
    )


def item_to_spec(item: TextFieldItem, page_index: int) -> TextFieldSpec:
    rect = item.boundingRect()
    bg = item.bg_color()
    return TextFieldSpec(
        page_index=page_index,
        x=item.pos().x(),
        y=item.pos().y(),
        width=rect.width(),
        height=rect.height(),
        text=item.toPlainText(),
        font_family=item.font_family(),
        font_size=item.font_pixel_size(),
        color=color_to_hex(item.text_color()),
        bg_color=color_to_hex(bg) if bg is not None else None,
        bold=item.is_bold(),
        italic=item.is_italic(),
    )


def spec_to_item(spec: TextFieldSpec) -> TextFieldItem:
    item = TextFieldItem(spec.text)
    item.set_font_family(spec.font_family)
    item.set_font_pixel_size(spec.font_size)
    item.set_bold(spec.bold)
    item.set_italic(spec.italic)
    item.set_text_color(hex_to_color(spec.color))
    item.set_bg_color(hex_to_color(spec.bg_color) if spec.bg_color is not None else None)
    item.setPos(spec.x, spec.y)
    return item
