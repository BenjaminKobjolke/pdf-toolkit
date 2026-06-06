"""Integration tests for text-field edit mode (offscreen Qt)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QGraphicsItem

from app.config.settings import Settings
from app.gui.crosshair_item import CrosshairItem
from app.gui.main_window import MainWindow
from app.gui.page_view import PageView
from app.gui.placement import PlacementController, PlacementMode
from app.gui.text_input_dialog import TextInputDialog
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


def test_add_text_field_enters_edit_mode(
    window: MainWindow, make_pdf: MakePdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The chooser is modal; pick Top-left without showing the dialog.
    monkeypatch.setattr(PlacementController, "_choose", lambda self: PlacementMode.TOP_LEFT)
    pdf = make_pdf([(300, 400)])
    window.open_pdf(pdf)
    assert not window._edit_bar.is_edit_mode()  # starts in Regular mode

    window.add_text_field()  # palette/button entry point

    assert window._edit_bar.is_edit_mode()  # auto-entered edit mode
    assert len(window._page_view.text_items()) == 1  # field actually added


def test_add_field_selects_new_field(window: MainWindow, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400)])
    window.open_pdf(pdf)
    window._controller.set_edit_mode(True)

    window._controller.add_field()

    item = window._page_view.text_items()[0]
    assert item.isSelected()  # fresh field is the active target


def test_enter_on_selected_field_opens_change_text_dialog(
    window: MainWindow, make_pdf: MakePdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[int] = []

    def reject_dialog(dialog: TextInputDialog) -> bool:
        calls.append(1)
        return False

    monkeypatch.setattr(TextInputDialog, "exec", reject_dialog)
    pdf = make_pdf([(300, 400)])
    window.open_pdf(pdf)
    window._controller.set_edit_mode(True)
    window._controller.add_field()  # selects the new field

    _press(window._page_view, Qt.Key.Key_Return)

    assert calls == [1]  # Enter reached change_text and opened the dialog


def test_enter_without_selection_does_not_open_dialog(
    window: MainWindow, make_pdf: MakePdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[int] = []

    def reject_dialog(dialog: TextInputDialog) -> bool:
        calls.append(1)
        return False

    monkeypatch.setattr(TextInputDialog, "exec", reject_dialog)
    pdf = make_pdf([(300, 400)])
    window.open_pdf(pdf)
    window._controller.set_edit_mode(True)
    window._controller.add_field()
    window._page_view.text_items()[0].setSelected(False)

    _press(window._page_view, Qt.Key.Key_Return)

    assert calls == []  # nothing selected → no dialog


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


def _crosshairs(view: PageView) -> list[CrosshairItem]:
    return [item for item in view.graphics_scene().items() if isinstance(item, CrosshairItem)]


def _begin_custom(window: MainWindow) -> list[QPointF | None]:
    """Start custom placement, recording each completion point (None = cancelled)."""
    done: list[QPointF | None] = []

    def on_done(point: QPointF | None) -> None:
        done.append(point)
        if point is not None:
            window._controller.add_field(point, centered=True)

    window._page_view.begin_custom_placement(on_done)
    return done


def test_add_field_page_center_centers_field(window: MainWindow, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400)])
    window.open_pdf(pdf)
    window._controller.set_edit_mode(True)
    center = window._page_view.page_center()

    window._controller.add_field(center, centered=True)

    item = window._page_view.text_items()[0]
    offset = item.boundingRect().center()
    assert item.pos().x() == pytest.approx(center.x() - offset.x())
    assert item.pos().y() == pytest.approx(center.y() - offset.y())


def test_add_field_view_center_lands_on_page(window: MainWindow, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400)])
    window.open_pdf(pdf)
    window._controller.set_edit_mode(True)

    window._controller.add_field(window._page_view.viewport_center_scene(), centered=True)

    item = window._page_view.text_items()[0]
    assert window._page_view.graphics_scene().sceneRect().contains(item.pos())


def test_custom_placement_enter_creates_field_at_crosshair(
    window: MainWindow, make_pdf: MakePdf
) -> None:
    pdf = make_pdf([(300, 400)])
    window.open_pdf(pdf)
    window._controller.set_edit_mode(True)

    _begin_custom(window)
    assert len(_crosshairs(window._page_view)) == 1  # marker visible while placing
    crosshair_pos = _crosshairs(window._page_view)[0].pos()
    _press(window._page_view, Qt.Key.Key_Return)

    item = window._page_view.text_items()[0]
    offset = item.boundingRect().center()
    assert item.pos().x() == pytest.approx(crosshair_pos.x() - offset.x())
    assert _crosshairs(window._page_view) == []  # marker removed on confirm


def test_custom_placement_arrow_moves_crosshair(window: MainWindow, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400)])
    window.open_pdf(pdf)
    window._controller.set_edit_mode(True)

    _begin_custom(window)
    start = _crosshairs(window._page_view)[0].pos()
    _press(window._page_view, Qt.Key.Key_Right)
    assert _crosshairs(window._page_view)[0].pos().x() == pytest.approx(start.x() + 10.0)

    _press(window._page_view, Qt.Key.Key_Down, shift=True)
    assert _crosshairs(window._page_view)[0].pos().y() == pytest.approx(start.y() + 1.0)


def test_custom_placement_escape_cancels(window: MainWindow, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400)])
    window.open_pdf(pdf)
    window._controller.set_edit_mode(True)

    done = _begin_custom(window)
    _press(window._page_view, Qt.Key.Key_Escape)

    assert done == [None]  # cancelled
    assert window._page_view.text_items() == ()  # no field added
    assert _crosshairs(window._page_view) == []  # marker removed


def test_custom_placement_click_creates_field(window: MainWindow, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400)])
    window.open_pdf(pdf)
    window._controller.set_edit_mode(True)

    _begin_custom(window)
    window._page_view._input.mouse_press(QPointF(120.0, 150.0))

    assert len(window._page_view.text_items()) == 1
    assert _crosshairs(window._page_view) == []


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


def test_export_embeds_text_into_working_copy_and_defers(
    window: MainWindow, make_pdf: MakePdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PySide6.QtWidgets import QMessageBox

    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: QMessageBox.StandardButton.Ok)
    pdf = make_pdf([(300, 400)])
    original_bytes = pdf.read_bytes()
    window.open_pdf(pdf)
    controller = window._controller
    controller.set_edit_mode(True)
    controller.add_field()

    window.export_text()

    # Fields are flattened into the working copy and cleared from the view.
    assert window._page_view.text_items() == ()
    assert window._working_doc.is_dirty()
    # The original on disk is untouched until the user saves.
    assert pdf.read_bytes() == original_bytes
    # No separate _text-embedded.pdf is written next to the original any more.
    assert not embedded_output_path(pdf).exists()


def test_autosave_persists_fields(window: MainWindow, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(300, 400)])
    window.open_pdf(pdf)
    controller = window._controller
    controller.set_edit_mode(True)
    controller.add_field()

    controller._save()  # what the debounce timer would call

    # Autosave writes to the working copy's sidecar, not the original (deferred).
    working = window._working_doc.working()
    assert working is not None
    doc = load_sidecar(working)
    assert len(doc.fields) == 1
    assert doc.fields[0].page_index == 0
    assert not sidecar_path(pdf).is_file()
