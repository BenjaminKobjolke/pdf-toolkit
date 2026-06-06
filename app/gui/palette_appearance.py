"""Apply :class:`PaletteSettings` to a palette dialog before it is shown.

Kept as a free function (no I/O) so the geometry/flags/opacity logic unit-tests
under the offscreen Qt platform without a running window. Called from
``MainWindow.open_command_palette`` after the dialog is built.
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QDialog

from app.config.palette_settings import (
    HEIGHT_PCT_MAX,
    HEIGHT_PCT_MIN,
    OPACITY_PCT_MAX,
    OPACITY_PCT_MIN,
    WIDTH_PCT_MAX,
    WIDTH_PCT_MIN,
    PaletteSettings,
)

_MIN_DIM = 200  # never shrink the palette below something usable


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def apply_appearance(dialog: QDialog, settings: PaletteSettings, window_size: QSize) -> None:
    """Resize, restyle, and reflag ``dialog`` from ``settings`` (relative to window)."""
    width_pct = _clamp(settings.width_pct, WIDTH_PCT_MIN, WIDTH_PCT_MAX)
    height_pct = _clamp(settings.height_pct, HEIGHT_PCT_MIN, HEIGHT_PCT_MAX)
    width = max(_MIN_DIM, window_size.width() * width_pct // 100)
    height = max(_MIN_DIM, window_size.height() * height_pct // 100)
    dialog.resize(width, height)

    if settings.font_pt > 0:
        font = dialog.font()
        font.setPointSize(settings.font_pt)
        dialog.setFont(font)

    opacity = _clamp(settings.opacity_pct, OPACITY_PCT_MIN, OPACITY_PCT_MAX)
    dialog.setWindowOpacity(opacity / 100)

    dialog.setWindowFlag(Qt.WindowType.FramelessWindowHint, settings.borderless)
