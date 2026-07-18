"""Unit tests for ReloadController (manual reload + auto-reload file watch).

The watcher's timeout handler is driven directly (``_on_timeout``) instead of
waiting on real filesystem-event delivery, which is flaky offscreen.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.config.reload_settings import ReloadSettings, ReloadSettingsStore
from app.config.zoom_settings import ZoomSettings
from app.gui.page_view import PageView
from app.gui.reload_controller import ReloadController
from tests.conftest import gui_backend


def make_controller(
    qapp: object,
    tmp_path: Path,
    source: Path | None,
) -> tuple[ReloadController, MagicMock, MagicMock, ReloadSettingsStore]:
    """Build a controller with mocked collaborators; return (ctl, open_pdf, page_view, store)."""
    from PySide6.QtCore import QObject

    store = ReloadSettingsStore(gui_backend(tmp_path))
    open_pdf = MagicMock()
    page_view = MagicMock(spec=PageView)
    page_view.current_page_index.return_value = 2
    page_view.current_zoom.return_value = ZoomSettings(fit=False, percent=150)
    parent = QObject()
    ctl = ReloadController(
        parent,
        store,
        lambda: source,
        open_pdf,
        page_view,
        MagicMock(),
    )
    # In the app the parent is the long-lived window; here keep the Qt parent
    # (and thus the C++ watcher/timer) alive for the controller's lifetime.
    ctl._test_parent = parent  # type: ignore[attr-defined]
    return ctl, open_pdf, page_view, store


@pytest.fixture
def watched_file(tmp_path: Path) -> Path:
    target = tmp_path / "doc.pdf"
    target.write_bytes(b"pdf")
    return target


def test_reload_without_document_is_noop(qapp: object, tmp_path: Path) -> None:
    ctl, open_pdf, _pv, _store = make_controller(qapp, tmp_path, None)
    ctl.reload()
    open_pdf.assert_not_called()


def test_reload_preserves_page_and_zoom(
    qapp: object, tmp_path: Path, watched_file: Path
) -> None:
    ctl, open_pdf, page_view, _store = make_controller(qapp, tmp_path, watched_file)
    ctl.reload()
    open_pdf.assert_called_once_with(watched_file)
    page_view.set_default_zoom.assert_called_once_with(False, 150)
    page_view.go_to_page.assert_called_once_with(2)


def test_session_toggle_arms_and_disarms_watcher(
    qapp: object, tmp_path: Path, watched_file: Path
) -> None:
    ctl, _open_pdf, _pv, _store = make_controller(qapp, tmp_path, watched_file)
    ctl.toggle_session_watch()
    assert str(watched_file) in ctl._watcher.files()
    ctl.toggle_session_watch()
    assert ctl._watcher.files() == []


def test_default_toggle_persists_and_applies_now(
    qapp: object, tmp_path: Path, watched_file: Path
) -> None:
    ctl, _open_pdf, _pv, store = make_controller(qapp, tmp_path, watched_file)
    ctl.toggle_watch_default()
    assert store.load() == ReloadSettings(watch_by_default=True)
    assert str(watched_file) in ctl._watcher.files()
    ctl.toggle_watch_default()
    assert store.load() == ReloadSettings(watch_by_default=False)
    assert ctl._watcher.files() == []


def test_open_document_arms_when_default_on(
    qapp: object, tmp_path: Path, watched_file: Path
) -> None:
    ctl, _open_pdf, _pv, store = make_controller(qapp, tmp_path, watched_file)
    store.save(ReloadSettings(watch_by_default=True))
    ctl.on_document_opened(watched_file)
    assert str(watched_file) in ctl._watcher.files()


def test_open_document_not_armed_when_default_off(
    qapp: object, tmp_path: Path, watched_file: Path
) -> None:
    ctl, _open_pdf, _pv, _store = make_controller(qapp, tmp_path, watched_file)
    ctl.on_document_opened(watched_file)
    assert ctl._watcher.files() == []


def test_open_document_resets_session_override(
    qapp: object, tmp_path: Path, watched_file: Path
) -> None:
    ctl, _open_pdf, _pv, _store = make_controller(qapp, tmp_path, watched_file)
    ctl.toggle_session_watch()
    ctl.on_document_opened(watched_file)
    assert ctl._watcher.files() == []


def test_close_document_disarms(qapp: object, tmp_path: Path, watched_file: Path) -> None:
    ctl, _open_pdf, _pv, _store = make_controller(qapp, tmp_path, watched_file)
    ctl.toggle_session_watch()
    ctl.on_document_closed()
    assert ctl._watcher.files() == []


def test_timeout_reloads(qapp: object, tmp_path: Path, watched_file: Path) -> None:
    ctl, open_pdf, _pv, _store = make_controller(qapp, tmp_path, watched_file)
    ctl.toggle_session_watch()
    ctl._on_timeout()
    open_pdf.assert_called_once_with(watched_file)


def test_self_save_suppresses_reload(
    qapp: object, tmp_path: Path, watched_file: Path
) -> None:
    ctl, open_pdf, _pv, _store = make_controller(qapp, tmp_path, watched_file)
    ctl.toggle_session_watch()
    ctl.mark_self_save()
    ctl._on_timeout()
    open_pdf.assert_not_called()


def test_timeout_rearms_dropped_path(
    qapp: object, tmp_path: Path, watched_file: Path
) -> None:
    ctl, open_pdf, _pv, _store = make_controller(qapp, tmp_path, watched_file)
    ctl.toggle_session_watch()
    ctl._watcher.removePath(str(watched_file))
    ctl._on_timeout()
    assert str(watched_file) in ctl._watcher.files()
    open_pdf.assert_called_once_with(watched_file)


def test_missing_file_gives_up_after_retries(
    qapp: object, tmp_path: Path, watched_file: Path
) -> None:
    ctl, open_pdf, _pv, _store = make_controller(qapp, tmp_path, watched_file)
    ctl.toggle_session_watch()
    watched_file.unlink()

    def fire() -> None:
        # A real single-shot timeout stops the timer before the handler runs.
        ctl._timer.stop()
        ctl._on_timeout()

    for _ in range(3):
        fire()
        assert ctl._timer.isActive()
    fire()
    assert not ctl._timer.isActive()
    open_pdf.assert_not_called()
