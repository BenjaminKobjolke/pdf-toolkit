"""Integration tests for the "Open thumbnails view from favorites" command."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.gui import commands
from app.gui.filter_list_dialog import ListEntry
from app.gui.main_window import MainWindow
from tests.conftest import MakePdf, fake_picker, gui_settings, silence_dialogs


@pytest.fixture
def window(qapp: object, tmp_path: Path) -> MainWindow:
    return MainWindow(gui_settings(tmp_path))


def _favorites_file(tmp_path: Path) -> Path:
    return gui_settings(tmp_path).favorites_file


def test_favorites_command_hidden_until_file_exists(window: MainWindow, tmp_path: Path) -> None:
    cmd = commands.find(window._registry, commands.OPEN_FAVORITES_THUMBNAILS)
    assert not cmd.is_enabled()
    _favorites_file(tmp_path).write_text("Docs|D:\\docs\n", encoding="utf-8")
    assert cmd.is_enabled()


def test_open_thumbnails_from_favorites_enters_grid(
    window: MainWindow, tmp_path: Path, make_pdf: MakePdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    first = make_pdf([(200, 300)], name="docs/one.pdf")
    make_pdf([(200, 300)], name="docs/two.pdf")
    _favorites_file(tmp_path).write_text(
        f"My Docs|{docs}\nBroken|{{{{Sync}}}}/GmbH\n", encoding="utf-8"
    )

    captured: list[ListEntry] = []
    fake_picker(monkeypatch, choose_index=0, captured=captured)
    # Works with no document open.
    commands.find(window._registry, commands.OPEN_FAVORITES_THUMBNAILS).run()

    assert [(e.title, e.subtitle) for e in captured] == [("My Docs", str(docs))]
    assert window.thumbnails_controller.is_active()
    assert window.thumbnails_controller.selected_path() == first


def test_file_commands_available_in_favorites_grid_without_document(
    window: MainWindow, tmp_path: Path, make_pdf: MakePdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    first = make_pdf([(200, 300)], name="docs/one.pdf")
    _favorites_file(tmp_path).write_text(f"My Docs|{docs}\n", encoding="utf-8")
    fake_picker(monkeypatch, choose_index=0, captured=[])
    commands.find(window._registry, commands.OPEN_FAVORITES_THUMBNAILS).run()

    fmt = window.current_format()
    file_info = commands.find(window._registry, commands.FILE_INFO)
    assert file_info.available(fmt) is True
    assert commands.find(window._registry, commands.RENAME_FILE).available(fmt) is True
    assert window._file_info_actions._source() == first


def test_open_thumbnails_from_favorites_empty_dir_shows_hint(
    window: MainWindow, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    _favorites_file(tmp_path).write_text(f"Empty|{empty}\n", encoding="utf-8")
    silence_dialogs(monkeypatch)
    fake_picker(monkeypatch, choose_index=0, captured=[])
    window.document_actions.open_thumbnails_from_favorites()

    assert not window.thumbnails_controller.is_active()
