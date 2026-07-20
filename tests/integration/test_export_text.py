"""Integration tests for the 'Export text to PDF' flow (offscreen Qt).

Exporting flattens the placed text fields, then either overwrites the original
(dropping the editable sidecar) or writes a new flattened file while the
original stays editable.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QGraphicsItem

from app.gui import confirm_dialog
from app.gui.confirm_dialog import DialogResult
from app.gui.export_actions import ExportActions
from app.gui.main_window import MainWindow
from app.pdf.sidecar import sidecar_path
from tests.conftest import MakePdf

_MOVABLE = QGraphicsItem.GraphicsItemFlag.ItemIsMovable


def _answer(monkeypatch: pytest.MonkeyPatch, result: DialogResult) -> None:
    """Make every confirm() return ``result`` and silence alert popups."""
    monkeypatch.setattr(confirm_dialog, "confirm", lambda *a, **k: result)
    monkeypatch.setattr(confirm_dialog, "show_message", lambda *a, **k: None)


def _open_with_one_field(window: MainWindow, pdf: Path) -> None:
    window.open_pdf(pdf)
    controller = window._controller
    controller.set_edit_mode(True)
    controller.add_field()


def test_export_overwrite_saves_to_original_and_drops_json(
    window: MainWindow, make_pdf: MakePdf, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _answer(monkeypatch, DialogResult.PRIMARY)
    pdf = make_pdf([(300, 400)])
    original_bytes = pdf.read_bytes()
    _open_with_one_field(window, pdf)

    window.export_text()

    # Text is flattened onto the original on disk and the editable data is gone.
    assert pdf.read_bytes() != original_bytes
    assert not sidecar_path(pdf).exists()
    assert list((tmp_path / "backup").glob(f"*-{pdf.name}"))
    assert window._page_view.text_items() == ()
    assert not window._working_doc.is_dirty()


def test_export_new_file_keeps_original_editable(
    window: MainWindow, make_pdf: MakePdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    _answer(monkeypatch, DialogResult.SECONDARY)
    monkeypatch.setattr(ExportActions, "_prompt_export_name", lambda self, default: "out.pdf")
    pdf = make_pdf([(300, 400)])
    original_bytes = pdf.read_bytes()
    _open_with_one_field(window, pdf)

    window.export_text()

    new_file = pdf.with_name("out.pdf")
    assert new_file.is_file()
    assert new_file.read_bytes() != original_bytes
    # The original and its session stay untouched and still editable.
    assert pdf.read_bytes() == original_bytes
    assert len(window._page_view.text_items()) == 1
    assert window._page_view.text_items()[0].flags() & _MOVABLE
    assert not sidecar_path(new_file).exists()


def test_export_cancel_does_nothing(
    window: MainWindow, make_pdf: MakePdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    _answer(monkeypatch, DialogResult.CANCEL)
    pdf = make_pdf([(300, 400)])
    original_bytes = pdf.read_bytes()
    _open_with_one_field(window, pdf)

    window.export_text()

    assert pdf.read_bytes() == original_bytes
    assert len(window._page_view.text_items()) == 1
    assert not pdf.with_name("out.pdf").exists()


def test_export_with_no_fields_reports_nothing(
    window: MainWindow, make_pdf: MakePdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.gui import strings

    asked: list[int] = []
    monkeypatch.setattr(confirm_dialog, "confirm", lambda *a, **k: asked.append(1))
    pdf = make_pdf([(300, 400)])
    original_bytes = pdf.read_bytes()
    window.open_pdf(pdf)  # no fields placed

    window.export_text()

    assert asked == []  # never prompted to overwrite
    # Told there is nothing to export — as a status-bar flash, not a dialog.
    assert window._mode_bar.flash_text() == strings.MSG_NO_TEXT_TO_EXPORT
    assert pdf.read_bytes() == original_bytes
