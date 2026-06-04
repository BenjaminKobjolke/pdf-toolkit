"""Integration tests for search + active-field commands on the window (offscreen Qt)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config.settings import Settings
from app.gui import commands
from app.gui.main_window import MainWindow
from tests.conftest import MakePdf, MakeSearchablePdf


@pytest.fixture
def window(qapp: object, tmp_path: Path) -> MainWindow:
    settings = Settings(
        backup_dir=tmp_path / "backup",
        log_level="INFO",
        recent_file=tmp_path / "recent.json",
    )
    return MainWindow(settings)


def _run(window: MainWindow, command_id: str) -> None:
    commands.find(commands.build_commands(window), command_id).run()


def test_search_pdf_jumps_and_highlights(
    window: MainWindow, make_searchable_pdf: MakeSearchablePdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    pdf = make_searchable_pdf(["nothing", "find me here"])
    window.open_pdf(pdf)

    # Drive the search dialog headlessly: pick the first provider result.
    def fake_exec(self: object) -> int:
        self._apply_filter("find")  # type: ignore[attr-defined]
        self.accept_current()  # type: ignore[attr-defined]
        return 1

    monkeypatch.setattr("app.gui.filter_list_dialog.FilterListDialog.exec", fake_exec)
    window.search_actions.search_pdf_text()

    assert window.page_view.current_page_one_based() == 2
    assert window.page_view.has_highlights()


def test_clear_highlights_command(
    window: MainWindow, make_searchable_pdf: MakeSearchablePdf
) -> None:
    window.open_pdf(make_searchable_pdf(["alpha"]))
    window.page_view.set_highlights([(1.0, 2.0, 3.0, 4.0)])
    _run(window, commands.CLEAR_HIGHLIGHTS)
    assert not window.page_view.has_highlights()


def test_active_field_font_size_command(
    window: MainWindow, make_pdf: MakePdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PySide6.QtWidgets import QInputDialog

    window.open_pdf(make_pdf([(300, 400)]))
    window.toggle_edit_mode()  # edit mode on
    window.controller.add_field()
    window.page_view.text_items()[0].setSelected(True)

    monkeypatch.setattr(QInputDialog, "getDouble", lambda *a, **k: (42.0, True))
    _run(window, commands.FIELD_FONT_SIZE)

    assert window.page_view.selected_text_item().font_pixel_size() == 42.0  # type: ignore[union-attr]


def test_field_commands_hidden_without_selection(window: MainWindow, make_pdf: MakePdf) -> None:
    window.open_pdf(make_pdf([(300, 400)]))
    registry = commands.build_commands(window)
    assert commands.find(registry, commands.FIELD_TOGGLE_BOLD).is_enabled() is False


def test_field_bg_transparent_sets_none(
    window: MainWindow, make_pdf: MakePdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PySide6.QtGui import QColor

    from app.gui.color_picker_dialog import ColorPickerDialog

    window.open_pdf(make_pdf([(300, 400)]))
    window.toggle_edit_mode()
    window.controller.add_field()
    item = window.page_view.text_items()[0]
    item.set_bg_color(QColor("#ff0000"))
    item.setSelected(True)

    # Pick "transparent" in the colour dialog.
    monkeypatch.setattr(ColorPickerDialog, "exec", lambda self: 1)
    monkeypatch.setattr(ColorPickerDialog, "chosen", lambda self: ColorPickerDialog.TRANSPARENT)
    _run(window, commands.FIELD_BG_COLOR)

    assert window.page_view.selected_text_item().bg_color() is None  # type: ignore[union-attr]
