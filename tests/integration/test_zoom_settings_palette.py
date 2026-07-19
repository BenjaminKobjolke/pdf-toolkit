"""Integration: default-zoom command, persistence, Remembered list, and startup apply."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtGui import QResizeEvent

from app.config.zoom_settings import ZoomSettings, ZoomSettingsStore
from app.gui import commands, settings_strings
from app.gui.filter_list_dialog import ListEntry
from app.gui.main_window import MainWindow
from app.gui.zoom_controller import _MODE_FIT, _ZOOM_ACTUAL
from app.storage.factory import make_backend
from tests.conftest import MakePdf, gui_backend, gui_settings


@pytest.fixture
def window(qapp: object, tmp_path: Path) -> MainWindow:
    return MainWindow(gui_settings(tmp_path))


class _FakeDialog:
    """Stand-in FilterListDialog that accepts the entry with ``pick_title``."""

    pick_title = ""

    def __init__(self, entries: list[ListEntry], *_args: object, **_kw: object) -> None:
        self._entries = entries

    def exec(self) -> int:
        return 1

    def chosen(self) -> object:
        return next(e for e in self._entries if e.title == self.pick_title)


def test_command_registered_and_enabled(window: MainWindow) -> None:
    command = commands.find(window._registry, commands.ZOOM_SET_DEFAULT)
    assert command.is_enabled() is True


def test_pick_preset_persists_and_applies(
    window: MainWindow, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class _Dialog(_FakeDialog):
        pick_title = settings_strings.ZOOM_PERCENT_FMT.format(n=50)

    monkeypatch.setattr("app.gui.zoom_settings_controller.FilterListDialog", _Dialog)
    commands.find(window._registry, commands.ZOOM_SET_DEFAULT).run()

    stored = ZoomSettingsStore(gui_backend(tmp_path)).load()
    assert stored == ZoomSettings(fit=False, percent=50)
    # Default pushed into the live view (no doc open → scaled factor set directly).
    assert window.page_view.zoom() == pytest.approx(0.5 * _ZOOM_ACTUAL)


def test_pick_fit_persists(
    window: MainWindow, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class _Dialog(_FakeDialog):
        pick_title = settings_strings.ZOOM_FIT_LABEL

    monkeypatch.setattr("app.gui.zoom_settings_controller.FilterListDialog", _Dialog)
    commands.find(window._registry, commands.ZOOM_SET_DEFAULT).run()

    assert ZoomSettingsStore(gui_backend(tmp_path)).load() == ZoomSettings(fit=True)


def test_pick_custom_prompts_for_percent(
    window: MainWindow, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.gui import number_input_dialog

    class _Dialog(_FakeDialog):
        pick_title = settings_strings.ZOOM_CUSTOM_LABEL

    monkeypatch.setattr("app.gui.zoom_settings_controller.FilterListDialog", _Dialog)
    monkeypatch.setattr(number_input_dialog, "prompt_int", lambda *a, **k: 175)
    commands.find(window._registry, commands.ZOOM_SET_DEFAULT).run()

    assert ZoomSettingsStore(gui_backend(tmp_path)).load() == ZoomSettings(fit=False, percent=175)


def test_store_in_remembered_list(window: MainWindow) -> None:
    labels = [store.label for store in window._remembered._stores]
    assert ZoomSettingsStore.LABEL in labels


def test_startup_applies_persisted_default(qapp: object, tmp_path: Path) -> None:
    settings = gui_settings(tmp_path)
    ZoomSettingsStore(make_backend(settings.database_url)).save(ZoomSettings(fit=False, percent=50))
    window = MainWindow(settings)
    assert window.page_view.zoom() == pytest.approx(0.5 * _ZOOM_ACTUAL)


def test_startup_fit_default_sets_fit_mode(qapp: object, tmp_path: Path) -> None:
    settings = gui_settings(tmp_path)
    ZoomSettingsStore(make_backend(settings.database_url)).save(ZoomSettings(fit=True))
    window = MainWindow(settings)
    assert window.page_view._zoom_ctl._mode == _MODE_FIT


def test_resize_refits_when_document_open(qapp: object, make_pdf: MakePdf) -> None:
    """A resize must re-fit (the initial fit is sized only after the window shows)."""
    from PySide6.QtCore import QSize

    from app.gui.page_view import PageView

    view = PageView()
    view.load(make_pdf([(300.0, 400.0)]))
    view.set_default_zoom(fit=True, percent=100)

    calls: list[int] = []
    original = view._zoom_ctl.reapply

    def track_reapply() -> None:
        calls.append(1)
        original()

    view._zoom_ctl.reapply = track_reapply  # type: ignore[method-assign]
    view.resizeEvent(QResizeEvent(QSize(800, 600), QSize(400, 300)))
    assert calls


def test_resize_ignored_without_document(qapp: object) -> None:
    from PySide6.QtCore import QSize

    from app.gui.page_view import PageView

    view = PageView()
    calls: list[int] = []

    def track_reapply() -> None:
        calls.append(1)

    view._zoom_ctl.reapply = track_reapply  # type: ignore[method-assign]
    view.resizeEvent(QResizeEvent(QSize(800, 600), QSize(400, 300)))
    assert not calls
