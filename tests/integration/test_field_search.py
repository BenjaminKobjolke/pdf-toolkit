"""Integration tests for text-field search + activation (offscreen Qt)."""

from __future__ import annotations

import pytest

from app.gui.edit_controller import EditController
from app.gui.page_view import PageView
from app.pdf.image_spec import SidecarDocument
from app.pdf.sidecar import save_sidecar
from app.pdf.text_spec import TextFieldSpec
from tests.conftest import MakePdf


def _spec(page_index: int, text: str) -> TextFieldSpec:
    return TextFieldSpec(
        page_index=page_index,
        x=20.0,
        y=30.0,
        width=0.0,
        height=0.0,
        text=text,
        font_family="Helvetica",
        font_size=18.0,
        color="#000000",
        bg_color=None,
        bold=False,
        italic=False,
    )


@pytest.fixture
def loaded(qapp: object, make_pdf: MakePdf) -> tuple[PageView, EditController]:
    pdf = make_pdf([(300, 400), (300, 400), (300, 400)])
    save_sidecar(
        pdf,
        SidecarDocument(
            fields=(
                _spec(0, "lala test"),
                _spec(1, "other"),
                _spec(2, "LALA two"),
            )
        ),
    )
    view = PageView()
    controller = EditController(view)
    controller.on_document_loaded(pdf)
    view.load(pdf)
    return view, controller


def test_field_hits_finds_across_pages(loaded: tuple[PageView, EditController]) -> None:
    _view, controller = loaded
    hits = controller.field_hits("lala")
    assert [(h.page_index, h.field_index) for h in hits] == [(0, 0), (2, 0)]


def test_field_hits_case_insensitive(loaded: tuple[PageView, EditController]) -> None:
    _view, controller = loaded
    assert controller.field_hits("LALA")
    assert controller.field_hits("lala")


def test_field_hits_empty_query(loaded: tuple[PageView, EditController]) -> None:
    _view, controller = loaded
    assert controller.field_hits("") == []


def test_activate_field_navigates_and_selects(loaded: tuple[PageView, EditController]) -> None:
    view, controller = loaded
    controller.activate_field(2, 0)
    assert view.current_page_one_based() == 3
    selected = view.selected_text_item()
    assert selected is not None
    assert selected.toPlainText() == "LALA two"


def test_selected_style_reflects_field(loaded: tuple[PageView, EditController]) -> None:
    view, controller = loaded
    controller.activate_field(0, 0)
    style = controller.selected_style()
    assert style is not None
    assert style.font_family == "Helvetica"
    assert style.color == "#000000"


def test_set_selected_text(loaded: tuple[PageView, EditController]) -> None:
    view, controller = loaded
    controller.activate_field(0, 0)
    controller.set_selected_text("changed")
    assert view.selected_text_item().toPlainText() == "changed"  # type: ignore[union-attr]
