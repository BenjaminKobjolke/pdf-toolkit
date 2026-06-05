"""Integration tests for clearing/flushing saved text fields (offscreen Qt)."""

from __future__ import annotations

from app.gui.edit_controller import EditController
from app.gui.page_view import PageView
from app.pdf.sidecar import load_sidecar, save_sidecar, sidecar_path
from app.pdf.text_spec import TextDocumentSpec, TextFieldSpec
from tests.conftest import MakePdf


def _spec() -> TextFieldSpec:
    return TextFieldSpec(
        page_index=0,
        x=20.0,
        y=30.0,
        width=0.0,
        height=0.0,
        text="Saved",
        font_family="Helvetica",
        font_size=18.0,
        color="#000000",
        bg_color=None,
        bold=False,
        italic=False,
    )


def test_clear_saved_fields_deletes_sidecar_and_items(qapp: object, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400)])
    save_sidecar(pdf, TextDocumentSpec(fields=(_spec(),)))
    view = PageView()
    controller = EditController(view)
    controller.on_document_loaded(pdf)
    view.load(pdf)  # page_changed restores the saved field onto the page
    assert view.text_items()  # field is present

    controller.clear_saved_fields()

    assert not sidecar_path(pdf).is_file()
    assert view.text_items() == ()


def test_clear_saved_fields_without_sidecar_is_safe(qapp: object, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400)])
    view = PageView()
    controller = EditController(view)
    controller.on_document_loaded(pdf)
    view.load(pdf)

    controller.clear_saved_fields()  # no sidecar on disk

    assert not sidecar_path(pdf).is_file()


def test_flush_writes_pending_fields(qapp: object, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400)])
    view = PageView()
    controller = EditController(view)
    controller.on_document_loaded(pdf)
    view.load(pdf)
    controller.set_edit_mode(True)
    controller.add_field()

    controller.flush()

    assert len(load_sidecar(pdf).fields) == 1


def test_flush_without_fields_creates_no_sidecar(qapp: object, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400)])
    view = PageView()
    controller = EditController(view)
    controller.on_document_loaded(pdf)  # no sidecar on disk
    view.load(pdf)
    controller.set_edit_mode(True)  # enter edit mode but add nothing

    controller.flush()

    assert not sidecar_path(pdf).is_file()


def test_flush_after_deleting_all_fields_removes_sidecar(
    qapp: object, make_pdf: MakePdf
) -> None:
    pdf = make_pdf([(300, 400)])
    save_sidecar(pdf, TextDocumentSpec(fields=(_spec(),)))
    view = PageView()
    controller = EditController(view)
    controller.on_document_loaded(pdf)
    view.load(pdf)  # page_changed restores the saved field
    controller.set_edit_mode(True)
    for item in view.text_items():
        item.setSelected(True)
    controller.delete_selected()

    controller.flush()

    assert not sidecar_path(pdf).is_file()
