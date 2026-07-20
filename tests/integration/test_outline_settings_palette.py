"""Integration: outline appearance commands, persistence, and Remembered list."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config.outline_settings import OutlineLineStyle, OutlineSettings, OutlineSettingsStore
from app.gui import commands
from app.gui.main_window import MainWindow
from app.gui.outline_style import active
from app.storage.factory import make_backend
from tests.conftest import gui_backend, gui_settings


@pytest.fixture
def window(qapp: object, tmp_path: Path) -> MainWindow:
    return MainWindow(gui_settings(tmp_path))


def test_outline_commands_registered(window: MainWindow) -> None:
    registry = window._registry
    for command_id in (commands.OUTLINE_WIDTH, commands.OUTLINE_STYLE, commands.OUTLINE_COLOR):
        command = commands.find(registry, command_id)
        assert command.is_enabled() is True


def test_set_width_persists_and_updates_holder(
    window: MainWindow, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.gui import number_input_dialog

    monkeypatch.setattr(number_input_dialog, "prompt_int", lambda *a, **k: 7)
    commands.find(window._registry, commands.OUTLINE_WIDTH).run()

    # Live holder reflects the change immediately.
    assert active().settings().width_px == 7
    # Persisted to disk and survives a fresh store load.
    assert OutlineSettingsStore(gui_backend(tmp_path)).load().width_px == 7


def test_set_style_persists(
    window: MainWindow, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.gui.filter_list_dialog import ListEntry

    class _FakeDialog:
        def __init__(self, entries: list[ListEntry], *_args: object, **_kw: object) -> None:
            self._entries = entries

        def exec(self) -> int:
            return 1

        def chosen(self) -> ListEntry:
            return next(e for e in self._entries if e.payload is OutlineLineStyle.SOLID)

    # pick_option constructs the dialog inside filter_list_dialog, so patch there.
    monkeypatch.setattr("app.gui.filter_list_dialog.FilterListDialog", _FakeDialog)
    commands.find(window._registry, commands.OUTLINE_STYLE).run()

    stored = OutlineSettingsStore(gui_backend(tmp_path)).load()
    assert stored.style is OutlineLineStyle.SOLID


def test_set_color_persists(
    window: MainWindow, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class _FakeColorDialog:
        def __init__(self, **_kw: object) -> None:
            pass

        def exec(self) -> int:
            return 1

        def chosen(self) -> str:
            return "#123456"

    monkeypatch.setattr("app.gui.color_picker_dialog.ColorPickerDialog", _FakeColorDialog)
    commands.find(window._registry, commands.OUTLINE_COLOR).run()

    assert active().settings().color == "#123456"
    stored = OutlineSettingsStore(gui_backend(tmp_path)).load()
    assert stored.color == "#123456"


def test_outline_store_in_remembered_list(window: MainWindow) -> None:
    labels = [store.label for store in window._remembered._stores]
    assert OutlineSettingsStore.LABEL in labels


def test_holder_loads_persisted_on_startup(qapp: object, tmp_path: Path) -> None:
    settings = gui_settings(tmp_path)
    OutlineSettingsStore(make_backend(settings.database_url)).save(
        OutlineSettings(width_px=9, style=OutlineLineStyle.SOLID, color="#0000FF")
    )
    MainWindow(settings)
    assert active().settings() == OutlineSettings(
        width_px=9, style=OutlineLineStyle.SOLID, color="#0000FF"
    )
