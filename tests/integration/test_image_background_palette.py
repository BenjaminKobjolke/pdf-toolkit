"""Integration: image-background command, persistence, render seam, Remembered list."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from app.config.image_background_settings import (
    ImageBackground,
    ImageBackgroundSettings,
    ImageBackgroundSettingsStore,
)
from app.gui import commands, render
from app.gui.main_window import MainWindow
from app.storage.factory import make_backend
from tests.conftest import gui_backend, gui_settings


@pytest.fixture(autouse=True)
def _reset_image_background() -> Iterator[None]:
    yield
    render.set_image_background(ImageBackgroundSettings())


@pytest.fixture
def window(qapp: object, tmp_path: Path) -> MainWindow:
    return MainWindow(gui_settings(tmp_path))


def test_image_background_command_registered(window: MainWindow) -> None:
    command = commands.find(window._registry, commands.IMAGE_BACKGROUND)
    assert command.is_enabled() is True


def test_set_background_persists_and_updates_render_seam(
    window: MainWindow, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.gui.filter_list_dialog import ListEntry

    class _FakeDialog:
        def __init__(self, entries: list[ListEntry], *_args: object, **_kw: object) -> None:
            self._entries = entries

        def exec(self) -> int:
            return 1

        def chosen(self) -> ListEntry:
            return next(e for e in self._entries if e.payload is ImageBackground.CHECKER)

    monkeypatch.setattr("app.gui.filter_list_dialog.FilterListDialog", _FakeDialog)
    commands.find(window._registry, commands.IMAGE_BACKGROUND).run()

    # Live render seam reflects the change immediately.
    assert render.active_image_background() is ImageBackground.CHECKER
    # Persisted to disk and survives a fresh store load.
    stored = ImageBackgroundSettingsStore(gui_backend(tmp_path)).load()
    assert stored.background is ImageBackground.CHECKER


def test_store_in_remembered_list(window: MainWindow) -> None:
    labels = [store.label for store in window._remembered._stores]
    assert ImageBackgroundSettingsStore.LABEL in labels


def test_persisted_background_applied_on_startup(qapp: object, tmp_path: Path) -> None:
    settings = gui_settings(tmp_path)
    ImageBackgroundSettingsStore(make_backend(settings.database_url)).save(
        ImageBackgroundSettings(background=ImageBackground.GREEN)
    )
    MainWindow(settings)
    assert render.active_image_background() is ImageBackground.GREEN
