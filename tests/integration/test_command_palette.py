"""Integration tests for palette/history wiring on the main window (offscreen Qt)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config.settings import Settings
from app.gui import commands
from app.gui.main_window import MainWindow
from app.pdf.sidecar import save_sidecar, sidecar_path
from app.pdf.text_spec import TextDocumentSpec, TextFieldSpec
from tests.conftest import MakePdf


@pytest.fixture
def window(qapp: object, tmp_path: Path) -> MainWindow:
    settings = Settings(
        backup_dir=tmp_path / "backup",
        log_level="INFO",
        recent_file=tmp_path / "recent.json",
    )
    return MainWindow(settings)


def _spec() -> TextFieldSpec:
    return TextFieldSpec(
        page_index=0,
        x=10.0,
        y=10.0,
        width=0.0,
        height=0.0,
        text="x",
        font_family="Helvetica",
        font_size=12.0,
        color="#000000",
        bg_color=None,
        bold=False,
        italic=False,
    )


def test_open_records_recent(window: MainWindow, make_pdf: MakePdf) -> None:
    pdf = make_pdf([(200, 300)])
    window.open_pdf(pdf)
    assert window._recent.load() == [pdf]


def test_palette_last_page_command_navigates(window: MainWindow, make_pdf: MakePdf) -> None:
    window.open_pdf(make_pdf([(200, 300), (200, 300), (200, 300)]))
    registry = commands.build_commands(window)
    commands.find(registry, commands.LAST_PAGE).run()
    assert window.page_view.current_page_one_based() == 3


def test_delete_saved_fields_command_removes_sidecar(
    window: MainWindow, make_pdf: MakePdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PySide6.QtWidgets import QMessageBox

    pdf = make_pdf([(200, 300)])
    save_sidecar(pdf, TextDocumentSpec(fields=(_spec(),)))
    window.open_pdf(pdf)
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)

    window.delete_saved_text_fields()

    assert not sidecar_path(pdf).is_file()


def test_close_document_resets_state(window: MainWindow, make_pdf: MakePdf) -> None:
    window.open_pdf(make_pdf([(200, 300)]))
    window.close_document()
    assert window.has_document() is False
    assert window.page_view.total_pages() == 0
