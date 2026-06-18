"""The live, shared dialog chrome — font size, opacity, and frameless flag.

A single :class:`PaletteSettings` value is registered as the module ``active()``
appearance; :class:`~app.gui.base_dialog.BaseDialog` reads it before a dialog is
shown so every small window adopts the command-palette look and honours the user's
palette font setting. :class:`~app.gui.palette_controller.PaletteController`
re-registers the settings whenever the user edits them, so the next dialog reflects
the change. Pure view: no persistence here.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog

from app.config.palette_settings import OPACITY_PCT_MAX, OPACITY_PCT_MIN, PaletteSettings


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def apply_chrome(dialog: QDialog, settings: PaletteSettings) -> None:
    """Apply font size, opacity, and frameless flag from ``settings`` (no resize).

    Shared by the palette applier (:func:`app.gui.palette_appearance.apply_appearance`)
    and every :class:`BaseDialog`, so the three inherited appearance properties have a
    single source of truth. ``font_pt == 0`` means "inherit the default size".
    """
    if settings.font_pt > 0:
        font = dialog.font()
        font.setPointSize(settings.font_pt)
        dialog.setFont(font)

    opacity = _clamp(settings.opacity_pct, OPACITY_PCT_MIN, OPACITY_PCT_MAX)
    dialog.setWindowOpacity(opacity / 100)

    dialog.setWindowFlag(Qt.WindowType.FramelessWindowHint, settings.borderless)


_active = PaletteSettings()


def active() -> PaletteSettings:
    """Return the shared palette settings every dialog adopts when shown."""
    return _active


def set_active(settings: PaletteSettings) -> None:
    """Register ``settings`` as the shared appearance returned by :func:`active`."""
    global _active
    _active = settings
