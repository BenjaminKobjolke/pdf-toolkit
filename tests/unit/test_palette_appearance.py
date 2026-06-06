"""Unit tests for applying palette appearance to a dialog (offscreen Qt)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QDialog

from app.config.palette_settings import PaletteSettings
from app.gui.palette_appearance import apply_appearance

_WINDOW = QSize(1000, 1000)


@pytest.fixture
def dialog(qapp: object) -> QDialog:
    return QDialog()


def test_size_tracks_window_percentages(dialog: QDialog) -> None:
    apply_appearance(dialog, PaletteSettings(width_pct=80, height_pct=60), _WINDOW)
    assert dialog.width() == 800
    assert dialog.height() == 600


def test_opacity_applied(dialog: QDialog) -> None:
    apply_appearance(dialog, PaletteSettings(opacity_pct=50), _WINDOW)
    assert dialog.windowOpacity() == pytest.approx(0.5, abs=0.01)


def test_borderless_sets_frameless_flag(dialog: QDialog) -> None:
    apply_appearance(dialog, PaletteSettings(borderless=True), _WINDOW)
    assert bool(dialog.windowFlags() & Qt.WindowType.FramelessWindowHint)


def test_not_borderless_keeps_frame(dialog: QDialog) -> None:
    apply_appearance(dialog, PaletteSettings(borderless=False), _WINDOW)
    assert not (dialog.windowFlags() & Qt.WindowType.FramelessWindowHint)


def test_font_applied_only_when_positive(dialog: QDialog) -> None:
    default_pt = dialog.font().pointSize()
    apply_appearance(dialog, PaletteSettings(font_pt=0), _WINDOW)
    assert dialog.font().pointSize() == default_pt
    apply_appearance(dialog, PaletteSettings(font_pt=18), _WINDOW)
    assert dialog.font().pointSize() == 18
