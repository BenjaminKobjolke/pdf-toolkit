"""Integration tests for rename-file and menu-bar toggle/persistence (offscreen Qt)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config.settings import Settings
from app.config.ui_state import UiState, UiStateStore
from app.gui.main_window import MainWindow
from app.pdf.sidecar import save_sidecar, sidecar_path
from app.pdf.text_spec import TextDocumentSpec
from tests.conftest import MakePdf


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        backup_dir=tmp_path / "backup",
        log_level="INFO",
        recent_file=tmp_path / "recent.json",
        ui_state_file=tmp_path / "ui_state.json",
    )


@pytest.fixture
def window(qapp: object, tmp_path: Path) -> MainWindow:
    return MainWindow(_settings(tmp_path))


def test_rename_moves_pdf_and_sidecar(
    window: MainWindow, make_pdf: MakePdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PySide6.QtWidgets import QInputDialog, QMessageBox

    pdf = make_pdf([(200, 300)], name="before.pdf")
    save_sidecar(pdf, TextDocumentSpec(fields=()))
    window.open_pdf(pdf)

    monkeypatch.setattr(QInputDialog, "getText", lambda *a, **k: ("after.pdf", True))
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)
    window.rename_file()

    target = pdf.with_name("after.pdf")
    assert target.is_file()
    assert not pdf.exists()
    assert sidecar_path(target).is_file()
    assert window.has_document()


def test_rename_appends_extension_when_missing(
    window: MainWindow, make_pdf: MakePdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PySide6.QtWidgets import QInputDialog, QMessageBox

    pdf = make_pdf([(200, 300)], name="before.pdf")
    window.open_pdf(pdf)
    monkeypatch.setattr(QInputDialog, "getText", lambda *a, **k: ("renamed", True))
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)
    window.rename_file()
    assert pdf.with_name("renamed.pdf").is_file()


def test_menu_hidden_by_default(window: MainWindow) -> None:
    assert window.menuBar().isHidden() is True


def test_toggle_menu_persists(window: MainWindow, tmp_path: Path) -> None:
    window.toggle_menu_bar()
    assert window.menuBar().isHidden() is False
    saved = UiStateStore(tmp_path / "ui_state.json").load()
    assert saved == UiState(menu_visible=True)


def test_saved_menu_state_reused_on_open(qapp: object, tmp_path: Path) -> None:
    UiStateStore(tmp_path / "ui_state.json").save(UiState(menu_visible=True))
    window = MainWindow(_settings(tmp_path))
    assert window.menuBar().isHidden() is False


def test_toolbars_hidden_by_default(window: MainWindow) -> None:
    assert window._bar.isHidden() is True
    assert window._edit_bar.isHidden() is True


def test_toggle_toolbar_persists(window: MainWindow, tmp_path: Path) -> None:
    window.toggle_toolbar()
    assert window._bar.isHidden() is False
    assert window._edit_bar.isHidden() is False
    saved = UiStateStore(tmp_path / "ui_state.json").load()
    assert saved.toolbar_visible is True


def test_saved_toolbar_state_reused_on_open(qapp: object, tmp_path: Path) -> None:
    UiStateStore(tmp_path / "ui_state.json").save(UiState(toolbar_visible=True))
    window = MainWindow(_settings(tmp_path))
    assert window._bar.isHidden() is False
