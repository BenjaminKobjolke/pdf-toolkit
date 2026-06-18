"""Integration: per-document zoom/page memory commands, persistence, and apply."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config.document_page import DocumentPageStore
from app.config.document_zoom import DocumentZoomStore
from app.config.zoom_settings import ZoomSettings
from app.gui import commands
from app.gui.main_window import MainWindow
from tests.conftest import MakePdf, gui_backend, gui_settings, silence_dialogs


@pytest.fixture
def window(qapp: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> MainWindow:
    silence_dialogs(monkeypatch)
    return MainWindow(gui_settings(tmp_path))


def _pick(monkeypatch: pytest.MonkeyPatch, payload: str) -> None:
    """Patch the memory menu dialog to accept the entry with ``payload``."""

    class _Dialog:
        def __init__(self, entries: list[object], **_kw: object) -> None:
            self._entries = entries

        def exec(self) -> int:
            return 1

        def chosen(self) -> object:
            return next(e for e in self._entries if e.payload == payload)  # type: ignore[attr-defined]

    monkeypatch.setattr("app.gui.document_memory_controller.FilterListDialog", _Dialog)


def _run(window: MainWindow, command_id: str) -> None:
    commands.find(window._registry, command_id).run()


def _doc(make_pdf: MakePdf) -> Path:
    return make_pdf([(100, 200), (120, 120), (150, 150), (90, 90)])


# --- remember + reopen ------------------------------------------------------


def test_remember_zoom_persists_and_reapplies_on_reopen(
    window: MainWindow, tmp_path: Path, make_pdf: MakePdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    pdf = _doc(make_pdf)
    window.open_pdf(pdf)
    window.page_view.set_default_zoom(False, 150)

    _pick(monkeypatch, "remember")
    _run(window, commands.DOC_ZOOM_REMEMBER)

    # Persisted for this document.
    assert DocumentZoomStore(gui_backend(tmp_path)).value_for(pdf) == ZoomSettings(
        fit=False, percent=150
    )
    # Reopening restores it.
    window.open_pdf(pdf)
    assert window.page_view.current_zoom() == ZoomSettings(fit=False, percent=150)


def test_remember_page_persists_and_reapplies_on_reopen(
    window: MainWindow, tmp_path: Path, make_pdf: MakePdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    pdf = _doc(make_pdf)
    window.open_pdf(pdf)
    window.page_view.go_to_page(2)  # page 3 (0-based)

    _pick(monkeypatch, "remember")
    _run(window, commands.DOC_PAGE_REMEMBER)

    assert DocumentPageStore(gui_backend(tmp_path)).value_for(pdf) == 2
    window.open_pdf(pdf)
    assert window.page_view.current_page_index() == 2


# --- auto-all is independent per dimension ----------------------------------


def test_auto_page_captures_on_switch_without_touching_zoom(
    window: MainWindow, tmp_path: Path, make_pdf: MakePdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    a = _doc(make_pdf)
    b = _doc(make_pdf)

    _pick(monkeypatch, "auto")
    _run(window, commands.DOC_PAGE_REMEMBER)  # page auto-remember ON, zoom stays OFF

    window.open_pdf(a)
    window.page_view.go_to_page(1)
    window.page_view.set_default_zoom(False, 175)
    window.open_pdf(b)  # switching captures page for A (auto), not zoom

    assert DocumentPageStore(gui_backend(tmp_path)).value_for(a) == 1
    assert DocumentZoomStore(gui_backend(tmp_path)).value_for(a) is None


# --- forget -----------------------------------------------------------------


def test_forget_zoom_leaves_page_intact(
    window: MainWindow, tmp_path: Path, make_pdf: MakePdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    pdf = _doc(make_pdf)
    window.open_pdf(pdf)
    window.page_view.set_default_zoom(False, 150)
    window.page_view.go_to_page(2)

    _pick(monkeypatch, "remember")
    _run(window, commands.DOC_ZOOM_REMEMBER)
    _run(window, commands.DOC_PAGE_REMEMBER)

    _pick(monkeypatch, "forget")
    _run(window, commands.DOC_ZOOM_REMEMBER)  # forget zoom only

    assert DocumentZoomStore(gui_backend(tmp_path)).value_for(pdf) is None
    assert DocumentPageStore(gui_backend(tmp_path)).value_for(pdf) == 2


def test_forget_all_clears_every_document(
    window: MainWindow, tmp_path: Path, make_pdf: MakePdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    a = _doc(make_pdf)
    b = _doc(make_pdf)
    for pdf in (a, b):
        window.open_pdf(pdf)
        window.page_view.go_to_page(1)
        _pick(monkeypatch, "remember")
        _run(window, commands.DOC_PAGE_REMEMBER)

    _pick(monkeypatch, "forget_all")
    _run(window, commands.DOC_PAGE_REMEMBER)

    store = DocumentPageStore(gui_backend(tmp_path))
    assert store.value_for(a) is None
    assert store.value_for(b) is None


# --- remembered-settings list + command registration ------------------------


def test_stores_in_remembered_list(window: MainWindow) -> None:
    labels = [store.label for store in window._remembered._stores]
    assert DocumentZoomStore.LABEL in labels
    assert DocumentPageStore.LABEL in labels


def test_commands_registered(window: MainWindow) -> None:
    for command_id in (commands.DOC_ZOOM_REMEMBER, commands.DOC_PAGE_REMEMBER):
        assert commands.find(window._registry, command_id).is_enabled() is True
