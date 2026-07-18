"""Integration tests: reload commands via the command palette."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config.reload_settings import ReloadSettingsStore
from app.gui import commands
from app.gui.main_window import MainWindow
from tests.conftest import MakePdf, gui_backend, gui_settings, silence_dialogs


@pytest.fixture
def window(qapp: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> MainWindow:
    silence_dialogs(monkeypatch)
    return MainWindow(gui_settings(tmp_path))


def test_reload_commands_registered(window: MainWindow) -> None:
    for command_id in (
        commands.RELOAD_DOC,
        commands.RELOAD_WATCH_SESSION,
        commands.RELOAD_WATCH_DEFAULT,
    ):
        commands.find(window._registry, command_id)


def test_reload_requires_document(window: MainWindow, make_pdf: MakePdf) -> None:
    assert commands.find(window._registry, commands.RELOAD_DOC).is_enabled() is False
    assert commands.find(window._registry, commands.RELOAD_WATCH_SESSION).is_enabled() is False
    assert commands.find(window._registry, commands.RELOAD_WATCH_DEFAULT).is_enabled() is True
    window.open_pdf(make_pdf([(200, 300)]))
    assert commands.find(window._registry, commands.RELOAD_DOC).is_enabled() is True
    assert commands.find(window._registry, commands.RELOAD_WATCH_SESSION).is_enabled() is True


def test_default_toggle_persists_flipped_value(window: MainWindow, tmp_path: Path) -> None:
    default = ReloadSettingsStore(gui_backend(tmp_path)).load().watch_by_default

    commands.find(window._registry, commands.RELOAD_WATCH_DEFAULT).run()

    assert ReloadSettingsStore(gui_backend(tmp_path)).load().watch_by_default is (not default)


def test_default_toggle_twice_restores_default(window: MainWindow, tmp_path: Path) -> None:
    default = ReloadSettingsStore(gui_backend(tmp_path)).load().watch_by_default

    commands.find(window._registry, commands.RELOAD_WATCH_DEFAULT).run()
    commands.find(window._registry, commands.RELOAD_WATCH_DEFAULT).run()

    assert ReloadSettingsStore(gui_backend(tmp_path)).load().watch_by_default is default


def test_store_in_remembered_list(window: MainWindow) -> None:
    labels = [store.label for store in window._remembered._stores]
    assert ReloadSettingsStore.LABEL in labels


def test_manual_reload_shows_changed_file(window: MainWindow, make_pdf: MakePdf) -> None:
    target = make_pdf([(200, 300)], name="doc.pdf")
    window.open_pdf(target)
    assert window.page_view.total_pages() == 1

    make_pdf([(200, 300), (200, 300)], name="doc.pdf")
    commands.find(window._registry, commands.RELOAD_DOC).run()

    assert window.page_view.total_pages() == 2
