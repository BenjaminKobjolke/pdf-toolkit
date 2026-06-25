"""Integration test: add a rectangle in the GUI, persist it, restore it, re-layer it."""

from __future__ import annotations

from PySide6.QtCore import QPointF

from app.gui.main_window import MainWindow
from app.pdf.sidecar import load_sidecar
from tests.conftest import MakePdf


def _open_in_edit_mode(window: MainWindow, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400), (300, 400)], name="doc.pdf")
    window.open_pdf(pdf)
    window.toggle_edit_mode()


def test_add_rect_persists_to_sidecar(window: MainWindow, make_pdf: MakePdf) -> None:
    _open_in_edit_mode(window, make_pdf)
    window.rects.add_rect(80.0, 60.0, "#ff8800", QPointF(40, 40))
    window.controller.flush()

    working = window._working_doc.working()
    assert working is not None
    doc = load_sidecar(working)
    assert len(doc.rects) == 1
    assert doc.rects[0].color == "#ff8800"
    assert (doc.rects[0].width, doc.rects[0].height) == (80.0, 60.0)


def test_rect_restored_after_page_navigation(window: MainWindow, make_pdf: MakePdf) -> None:
    _open_in_edit_mode(window, make_pdf)
    window.rects.add_rect(80.0, 60.0, "#ff8800", QPointF(40, 40))

    window.page_view.show_next()
    assert window.page_view.rect_items() == ()
    window.page_view.show_prev()
    assert len(window.page_view.rect_items()) == 1


def test_bring_to_front_reorders_across_types(window: MainWindow, make_pdf: MakePdf) -> None:
    _open_in_edit_mode(window, make_pdf)
    # Add a rect, then a field: the field lands on top (higher z) by default.
    window.rects.add_rect(80.0, 60.0, "#ff8800", QPointF(40, 40))
    window.controller.add_field(QPointF(50, 50))
    rect = window.page_view.rect_items()[0]
    field = window.page_view.text_items()[0]
    assert rect.zValue() < field.zValue()

    # Select the rect and bring it to the front; now it must outrank the field.
    window.page_view.graphics_scene().clearSelection()
    rect.setSelected(True)
    window.layer_actions.bring_to_front()
    assert rect.zValue() > field.zValue()
