"""Integration tests: reuse-window toggle via the command palette."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config.instance_settings import InstanceSettingsStore
from app.gui import commands
from app.gui.main_window import MainWindow
from tests.conftest import gui_backend, gui_settings, silence_dialogs


@pytest.fixture
def window(qapp: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> MainWindow:
    silence_dialogs(monkeypatch)
    return MainWindow(gui_settings(tmp_path))


def test_command_registered_and_enabled(window: MainWindow) -> None:
    command = commands.find(window._registry, commands.REUSE_WINDOW)
    assert command.is_enabled()
    assert command.available(None)  # no document needed


def test_toggle_persists_flipped_value(window: MainWindow, tmp_path: Path) -> None:
    default = InstanceSettingsStore(gui_backend(tmp_path)).load().reuse_window

    commands.find(window._registry, commands.REUSE_WINDOW).run()

    assert InstanceSettingsStore(gui_backend(tmp_path)).load().reuse_window is (not default)


def test_toggle_twice_restores_default(window: MainWindow, tmp_path: Path) -> None:
    default = InstanceSettingsStore(gui_backend(tmp_path)).load().reuse_window

    commands.find(window._registry, commands.REUSE_WINDOW).run()
    commands.find(window._registry, commands.REUSE_WINDOW).run()

    assert InstanceSettingsStore(gui_backend(tmp_path)).load().reuse_window is default


def test_store_in_remembered_list(window: MainWindow) -> None:
    labels = [store.label for store in window._remembered._stores]
    assert InstanceSettingsStore.LABEL in labels
