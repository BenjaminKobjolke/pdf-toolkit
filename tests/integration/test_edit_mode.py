"""Integration tests for text-field edit mode (offscreen Qt)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QGraphicsItem

from app.config.settings import Settings
from app.gui.main_window import MainWindow
from app.gui.page_view import PageView
from app.pdf.sidecar import load_sidecar, save_sidecar, sidecar_path
from app.pdf.text_overlay import embedded_output_path
from app.pdf.text_spec import TextDocumentSpec, TextFieldSpec
from tests.conftest import MakePdf

_MOVABLE = QGraphicsItem.GraphicsItemFlag.ItemIsMovable


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


def _press(view: PageView, key: Qt.Key, shift: bool = False) -> None:
    mods = Qt.KeyboardModifier.ShiftModifier if shift else Qt.KeyboardModifier.NoModifier
    view.keyPressEvent(QKeyEvent(QKeyEvent.Type.KeyPress, key, mods))


@pytest.fixture
def window(qapp: object, tmp_path: Path) -> MainWindow:
    settings = Settings(
        backup_dir=tmp_path / "backup",
        log_level="INFO",
        recent_file=tmp_path / "recent.json",
    )
    return MainWindow(settings)


def test_saved_fields_show_without_edit_mode(window: MainWindow, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400)])
    save_sidecar(pdf, TextDocumentSpec(fields=(_spec(),)))

    window.open_pdf(pdf)

    items = window._page_view.text_items()
    assert len(items) == 1  # visible without toggling edit mode
    assert not (items[0].flags() & _MOVABLE)  # but not editable yet

    window._controller.set_edit_mode(True)
    assert items[0].flags() & _MOVABLE  # editable once edit mode is on


def test_add_field_only_in_edit_mode(window: MainWindow, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400)])
    window.open_pdf(pdf)

    window._controller.add_field()  # not in edit mode yet
    assert window._page_view.text_items() == ()

    window._controller.set_edit_mode(True)
    window._controller.add_field()
    assert len(window._page_view.text_items()) == 1


def test_add_text_field_enters_edit_mode(window: MainWindow, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400)])
    window.open_pdf(pdf)
    assert not window._edit_bar.is_edit_mode()  # starts in Regular mode

    window.add_text_field()  # palette/button entry point

    assert window._edit_bar.is_edit_mode()  # auto-entered edit mode
    assert len(window._page_view.text_items()) == 1  # field actually added


def test_delete_selected_removes_field(window: MainWindow, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400)])
    window.open_pdf(pdf)
    controller = window._controller
    controller.set_edit_mode(True)
    controller.add_field()

    window._page_view.text_items()[0].setSelected(True)
    controller.delete_selected()

    assert window._page_view.text_items() == ()


def test_arrow_keys_nudge_selected_field(window: MainWindow, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400)])
    window.open_pdf(pdf)
    window._controller.set_edit_mode(True)
    window._controller.add_field()
    item = window._page_view.text_items()[0]
    item.setSelected(True)
    start = item.pos()

    _press(window._page_view, Qt.Key.Key_Right)
    assert item.pos().x() == pytest.approx(start.x() + 10.0)

    _press(window._page_view, Qt.Key.Key_Down, shift=True)
    assert item.pos().y() == pytest.approx(start.y() + 1.0)


def test_arrow_keys_ignored_without_selection(window: MainWindow, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400)])
    window.open_pdf(pdf)
    window._controller.set_edit_mode(True)
    window._controller.add_field()
    item = window._page_view.text_items()[0]
    item.setSelected(False)
    start = item.pos()

    _press(window._page_view, Qt.Key.Key_Right)
    assert item.pos() == start


def test_fields_restore_on_navigation(window: MainWindow, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400), (300, 400)])
    window.open_pdf(pdf)
    controller = window._controller
    controller.set_edit_mode(True)
    controller.add_field()

    window._page_view.show_next()
    assert window._page_view.text_items() == ()  # page 2 has no fields

    window._page_view.show_prev()
    assert len(window._page_view.text_items()) == 1  # page 1 field restored


def test_export_writes_embedded_copy_and_keeps_source(
    window: MainWindow, make_pdf: MakePdf
) -> None:
    pdf = make_pdf([(300, 400)])
    window.open_pdf(pdf)
    controller = window._controller
    controller.set_edit_mode(True)
    controller.add_field()

    result = controller.export(pdf)

    output = embedded_output_path(pdf)
    assert result.ok
    assert output.name.endswith("_text-embedded.pdf")
    assert output.is_file()  # embedded copy written
    assert pdf.is_file()  # original untouched
    assert sidecar_path(pdf).is_file()


def test_autosave_persists_fields(window: MainWindow, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400)])
    window.open_pdf(pdf)
    controller = window._controller
    controller.set_edit_mode(True)
    controller.add_field()

    controller._save()  # what the debounce timer would call

    doc = load_sidecar(pdf)
    assert len(doc.fields) == 1
    assert doc.fields[0].page_index == 0
