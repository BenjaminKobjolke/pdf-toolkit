"""The live outline holder builds the right pen and draws on demand."""

from __future__ import annotations

from unittest.mock import MagicMock

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter

from app.config.outline_settings import OutlineLineStyle, OutlineSettings
from app.gui.outline_style import OutlineStyle


def test_pen_reflects_width_color_and_style(qapp: object) -> None:
    holder = OutlineStyle(
        OutlineSettings(width_px=5, style=OutlineLineStyle.SOLID, color="#00FF00")
    )
    pen = holder.pen()
    assert pen.widthF() == 5.0
    assert pen.style() == Qt.PenStyle.SolidLine
    assert pen.color().name(pen.color().NameFormat.HexRgb).upper() == "#00FF00"
    assert pen.isCosmetic()


def test_dashed_maps_to_dash_line(qapp: object) -> None:
    holder = OutlineStyle(OutlineSettings(style=OutlineLineStyle.DASHED))
    assert holder.pen().style() == Qt.PenStyle.DashLine


def test_set_updates_subsequent_pen(qapp: object) -> None:
    holder = OutlineStyle(OutlineSettings(width_px=1))
    holder.set(OutlineSettings(width_px=8))
    assert holder.pen().widthF() == 8.0


def test_draw_strokes_rect_without_fill(qapp: object) -> None:
    holder = OutlineStyle(OutlineSettings())
    painter = MagicMock(spec=QPainter)
    rect = object()
    holder.draw(painter, rect)  # type: ignore[arg-type]
    painter.setBrush.assert_called_once_with(Qt.BrushStyle.NoBrush)
    painter.drawRect.assert_called_once_with(rect)
    painter.setPen.assert_called_once()
