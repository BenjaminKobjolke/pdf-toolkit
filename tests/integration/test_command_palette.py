"""Integration tests for palette/history wiring on the main window (offscreen Qt)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config.settings import Settings
from app.gui import commands
from app.gui.filter_list_dialog import ListEntry
from app.gui.main_window import MainWindow
from app.gui.palette_entries import build_palette_entries
from app.pdf.image_spec import SidecarDocument
from app.pdf.sidecar import save_sidecar, sidecar_path
from app.pdf.text_spec import TextFieldSpec
from tests.conftest import MakePdf, gui_settings


def _settings(tmp_path: Path) -> Settings:
    return gui_settings(tmp_path)


@pytest.fixture
def window(qapp: object, tmp_path: Path) -> MainWindow:
    return MainWindow(_settings(tmp_path))


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
    save_sidecar(pdf, SidecarDocument(fields=(_spec(),)))
    window.open_pdf(pdf)
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: QMessageBox.StandardButton.Ok)

    window.delete_saved_text_fields()

    # Deferred: the original sidecar is removed only on save.
    assert sidecar_path(pdf).is_file()
    window.save_changes()
    assert not sidecar_path(pdf).is_file()


def test_close_document_resets_state(window: MainWindow, make_pdf: MakePdf) -> None:
    window.open_pdf(make_pdf([(200, 300)]))
    window.close_document()
    assert window.has_document() is False
    assert window.page_view.total_pages() == 0


def test_palette_entries_float_recent_and_bold_top(window: MainWindow) -> None:
    window._command_history.add(commands.OPEN_HISTORY)
    window._command_history.add(commands.OPEN)  # most-recent
    entries = build_palette_entries(
        window._registry, window._command_history.load(), window.current_keymap()
    )

    # Most-recent first, then the next-recent.
    assert entries[0].payload.command_id == commands.OPEN
    assert entries[1].payload.command_id == commands.OPEN_HISTORY
    # Only the top enabled entry is bolded.
    assert entries[0].bold is True
    assert sum(1 for e in entries if e.bold) == 1


def test_palette_records_command_on_run(
    window: MainWindow, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = commands.find(window._registry, commands.TOGGLE_STATUSBAR)

    class _FakeDialog:
        def __init__(self, entries: list[ListEntry], **_kw: object) -> None:
            self._entries = entries

        def exec(self) -> int:
            return 1

        def chosen(self) -> ListEntry | None:
            return next(e for e in self._entries if e.payload is target)

    monkeypatch.setattr("app.gui.palette_actions.FilterListDialog", _FakeDialog)
    monkeypatch.setattr(window._palette, "apply_to", lambda *a, **k: None)

    window.open_command_palette()

    assert window._command_history.load()[0] == commands.TOGGLE_STATUSBAR
    # Survives a fresh window against the same store path.
    reopened = MainWindow(_settings(tmp_path))
    assert reopened._command_history.load()[0] == commands.TOGGLE_STATUSBAR
