"""Unit test for FieldActions.scale_font (offscreen Qt)."""

from __future__ import annotations

from app.gui.main_window import MainWindow
from tests.conftest import MakePdf


def test_scale_font_multiplies_size(window: MainWindow, make_pdf: MakePdf) -> None:
    window.open_pdf(make_pdf([(300, 400)]))
    window.toggle_edit_mode()
    window.controller.add_field()  # adds at the default position and selects it

    before = window.controller.selected_style()
    assert before is not None
    window.field_actions.scale_font(2.0)
    after = window.controller.selected_style()
    assert after is not None
    assert after.font_size == before.font_size * 2.0
