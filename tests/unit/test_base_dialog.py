"""Unit tests for the shared dialog base that adopts the active palette chrome."""

from __future__ import annotations

from app.config.palette_settings import PaletteSettings
from app.gui import dialog_appearance
from app.gui.base_dialog import BaseDialog


def test_dialog_adopts_active_font(qapp: object) -> None:
    original = dialog_appearance.active()
    try:
        dialog_appearance.set_active(PaletteSettings(font_pt=27))
        dialog = BaseDialog()
        dialog.apply_active_chrome()
        assert dialog.font().pointSize() == 27
    finally:
        dialog_appearance.set_active(original)


def test_dialog_reflects_changed_active_setting(qapp: object) -> None:
    original = dialog_appearance.active()
    try:
        dialog_appearance.set_active(PaletteSettings(font_pt=12))
        dialog = BaseDialog()
        dialog_appearance.set_active(PaletteSettings(font_pt=30))
        dialog.apply_active_chrome()
        assert dialog.font().pointSize() == 30
    finally:
        dialog_appearance.set_active(original)
