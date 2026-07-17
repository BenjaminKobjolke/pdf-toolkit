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
from tests.conftest import MakePdf, gui_settings, silence_dialogs


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
    pdf = make_pdf([(200, 300)])
    save_sidecar(pdf, SidecarDocument(fields=(_spec(),)))
    window.open_pdf(pdf)
    silence_dialogs(monkeypatch)

    window.delete_saved_text_fields()

    # Deferred: the original sidecar is removed only on save.
    assert sidecar_path(pdf).is_file()
    window.save_changes()
    assert not sidecar_path(pdf).is_file()


def test_copy_name_no_ext_command_gated_by_document(window: MainWindow, make_pdf: MakePdf) -> None:
    registry = commands.build_commands(window)
    assert commands.find(registry, commands.COPY_FILE_NAME_NO_EXT).is_enabled() is False
    window.open_pdf(make_pdf([(200, 300)]))
    registry = commands.build_commands(window)
    assert commands.find(registry, commands.COPY_FILE_NAME_NO_EXT).is_enabled() is True


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


def test_open_folder_from_history_lists_unique_folders_and_opens_last_file(
    window: MainWindow, tmp_path: Path, make_pdf: MakePdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    first = make_pdf([(200, 300)], name="a/one.pdf")
    second = make_pdf([(200, 300)], name="b/two.pdf")
    third = make_pdf([(200, 300)], name="a/three.pdf")
    for pdf in (first, second, third):
        window.open_pdf(pdf)

    captured: list[ListEntry] = []

    class _FakeDialog:
        def __init__(self, entries: list[ListEntry], **_kw: object) -> None:
            captured.extend(entries)

        def exec(self) -> int:
            return 1

        def chosen(self) -> ListEntry | None:
            return captured[1]  # folder "b"

    monkeypatch.setattr("app.gui.document_actions.FilterListDialog", _FakeDialog)
    window.open_folder_from_history()

    # Unique folders, most-recent-first; payload is that folder's last-opened file.
    assert [e.subtitle for e in captured] == [str(third.parent), str(second.parent)]
    assert [e.payload for e in captured] == [third, second]
    assert window._source == second


def test_dialog_size_command_persists(
    window: MainWindow, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.gui.number_input_dialog.prompt_int", lambda *a, **k: 45)
    commands.find(window._registry, commands.DIALOG_SIZE).run()

    reopened = MainWindow(_settings(tmp_path))
    assert reopened.palette_controller._settings.dialog_size_pct == 45


def test_file_browser_sizes_relative_to_parent_window(
    window: MainWindow, tmp_path: Path
) -> None:
    from app.gui import file_browser_strings as fbs
    from app.gui.file_browser_dialog import FileBrowserDialog, _Mode

    window.resize(1000, 800)
    dialog = FileBrowserDialog(
        mode=_Mode.OPEN, title="t", filt=fbs.FILTER_ALL, start=tmp_path, parent=window
    )
    # Default dialog_size_pct = 60 → 60% of the 1000x800 parent window.
    assert (dialog.width(), dialog.height()) == (600, 480)


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
