"""Integration test: add an image in the GUI, persist it, and restore it."""

from __future__ import annotations

from PySide6.QtCore import QPointF

from app.gui.main_window import MainWindow
from app.pdf.sidecar import load_sidecar
from tests.conftest import MakeImage, MakePdf


def _open_in_edit_mode(window: MainWindow, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400), (300, 400)], name="doc.pdf")
    window.open_pdf(pdf)
    window.toggle_edit_mode()  # turns edit mode on for text + image controllers


def test_add_image_persists_to_sidecar(
    window: MainWindow, make_pdf: MakePdf, make_image: MakeImage
) -> None:
    _open_in_edit_mode(window, make_pdf)
    img = make_image("png", name="sig.png")
    window.images.add_image(img, str(img), True, QPointF(40, 40))
    window.controller.flush()

    working = window._working_doc.working()
    assert working is not None
    doc = load_sidecar(working)
    assert len(doc.images) == 1
    assert doc.images[0].absolute is True


def test_image_restored_after_page_navigation(
    window: MainWindow, make_pdf: MakePdf, make_image: MakeImage
) -> None:
    _open_in_edit_mode(window, make_pdf)
    img = make_image("png", name="sig.png")
    window.images.add_image(img, str(img), True, QPointF(40, 40))

    window.page_view.show_next()
    assert window.page_view.image_items() == ()
    window.page_view.show_prev()
    assert len(window.page_view.image_items()) == 1


def test_delete_image_clears_sidecar(
    window: MainWindow, make_pdf: MakePdf, make_image: MakeImage
) -> None:
    _open_in_edit_mode(window, make_pdf)
    img = make_image("png", name="sig.png")
    window.images.add_image(img, str(img), True, QPointF(40, 40))
    window.images.delete_selected()
    window.controller.flush()

    working = window._working_doc.working()
    assert working is not None
    assert load_sidecar(working).images == ()
