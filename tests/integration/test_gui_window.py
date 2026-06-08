"""Integration tests for the GUI window wiring (offscreen Qt)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QMessageBox

from app.config.settings import Settings
from app.config.window_geometry import WindowGeometry, WindowGeometryStore
from app.gui.main_window import MainWindow
from tests.conftest import MakePdf, PageSizesOf, gui_settings


def _settings(tmp_path: Path) -> Settings:
    return gui_settings(tmp_path)


@pytest.fixture
def window(qapp: object, tmp_path: Path) -> MainWindow:
    return MainWindow(_settings(tmp_path))


def test_delete_current_page_shrinks_document(
    window: MainWindow,
    monkeypatch: pytest.MonkeyPatch,
    make_pdf: MakePdf,
    page_sizes_of: PageSizesOf,
) -> None:
    pdf = make_pdf([(100, 200), (300, 400), (120, 120)])
    window.open_pdf(pdf)
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: QMessageBox.StandardButton.Ok)

    window.page_actions.delete_current_page()

    # Deferred: the view + working copy shrink; the original is intact until save.
    assert window._page_view.total_pages() == 2
    assert window._working_doc.is_dirty()
    assert page_sizes_of(pdf) == [(100, 200), (300, 400), (120, 120)]

    window.save_changes()
    assert page_sizes_of(pdf) == [(300, 400), (120, 120)]


def test_swap_pages_through_window(
    window: MainWindow,
    monkeypatch: pytest.MonkeyPatch,
    make_pdf: MakePdf,
    page_sizes_of: PageSizesOf,
) -> None:
    pdf = make_pdf([(100, 200), (300, 400)])
    window.open_pdf(pdf)
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: QMessageBox.StandardButton.Ok)

    window.page_actions.swap()

    # Deferred: the original changes only after an explicit save.
    assert page_sizes_of(pdf) == [(100, 200), (300, 400)]
    window.save_changes()
    assert page_sizes_of(pdf) == [(300, 400), (100, 200)]


def test_invalid_swap_reports_error_and_keeps_file(
    window: MainWindow,
    monkeypatch: pytest.MonkeyPatch,
    make_pdf: MakePdf,
    page_sizes_of: PageSizesOf,
) -> None:
    pdf = make_pdf([(100, 200), (300, 400), (120, 120)])
    window.open_pdf(pdf)
    captured: list[str] = []
    monkeypatch.setattr(
        QMessageBox, "critical", lambda parent, title, msg, *a, **k: captured.append(msg)
    )

    window.page_actions.swap()

    assert captured  # an error dialog was shown
    assert page_sizes_of(pdf) == [(100, 200), (300, 400), (120, 120)]


def test_window_geometry_restored_on_construct(qapp: object, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    WindowGeometryStore(settings.window_file).save(
        WindowGeometry(x=120, y=90, width=640, height=480)
    )
    win = MainWindow(settings)
    assert win.width() == 640
    assert win.height() == 480


def test_offscreen_geometry_pulled_back_on_screen(qapp: object, tmp_path: Path) -> None:
    # Saved position points at a monitor that no longer exists (display changed):
    # the window must be relocated onto a connected screen, not left invisible.
    from PySide6.QtGui import QGuiApplication

    settings = _settings(tmp_path)
    WindowGeometryStore(settings.window_file).save(
        WindowGeometry(x=99999, y=99999, width=640, height=480)
    )
    win = MainWindow(settings)
    assert QGuiApplication.screenAt(win.frameGeometry().center()) is not None


def test_close_event_persists_geometry(qapp: object, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    win = MainWindow(settings)
    win.resize(700, 500)
    win.close()
    geom = WindowGeometryStore(settings.window_file).load()
    assert geom is not None
    assert (geom.width, geom.height) == (700, 500)


def test_toggle_statusbar_hides_and_persists(qapp: object, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    win = MainWindow(settings)
    assert win._mode_bar.isHidden() is False

    win.toggle_statusbar()
    assert win._mode_bar.isHidden() is True

    # Persisted: a fresh window restores the hidden status bar.
    reopened = MainWindow(settings)
    assert reopened._mode_bar.isHidden() is True


def test_toggle_fullscreen_is_session_only(qapp: object, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    win = MainWindow(settings)
    win.toggle_fullscreen()
    assert win.isFullScreen() is True
    win.toggle_fullscreen()
    assert win.isFullScreen() is False
