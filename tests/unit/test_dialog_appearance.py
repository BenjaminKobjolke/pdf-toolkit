"""Unit tests for the shared dialog-chrome holder and applier."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog

from app.config.palette_settings import PaletteSettings
from app.gui import dialog_appearance


def test_apply_chrome_sets_font_size(qapp: object) -> None:
    dialog = QDialog()
    dialog_appearance.apply_chrome(dialog, PaletteSettings(font_pt=24))
    assert dialog.font().pointSize() == 24


def test_apply_chrome_skips_font_when_zero(qapp: object) -> None:
    dialog = QDialog()
    before = dialog.font().pointSize()
    dialog_appearance.apply_chrome(dialog, PaletteSettings(font_pt=0))
    assert dialog.font().pointSize() == before


def test_apply_chrome_sets_opacity(qapp: object) -> None:
    dialog = QDialog()
    dialog_appearance.apply_chrome(dialog, PaletteSettings(opacity_pct=50))
    assert dialog.windowOpacity() == pytest.approx(0.5, abs=0.01)


def test_apply_chrome_sets_frameless_flag(qapp: object) -> None:
    dialog = QDialog()
    dialog_appearance.apply_chrome(dialog, PaletteSettings(borderless=True))
    assert bool(dialog.windowFlags() & Qt.WindowType.FramelessWindowHint)


def test_set_active_round_trips(qapp: object) -> None:
    original = dialog_appearance.active()
    try:
        settings = PaletteSettings(font_pt=18)
        dialog_appearance.set_active(settings)
        assert dialog_appearance.active() is settings
    finally:
        dialog_appearance.set_active(original)
