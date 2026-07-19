"""Unit tests for LifecycleActions (document open/close/shutdown branch logic).

The happy-path open flow is pinned by the integration suite through the
window's delegators; these tests cover only the guard branches.
"""

from __future__ import annotations

from pathlib import Path
from typing import cast
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QWidget

from app.config.recent_files import RecentFilesStore
from app.gui import confirm_dialog, file_browser_model, strings
from app.gui.chrome import ChromeController
from app.gui.controls import OperationBar
from app.gui.document_memory_controller import DocumentMemoryGroup
from app.gui.edit_bar import EditBar
from app.gui.edit_controller import EditController
from app.gui.image_controller import ImageController
from app.gui.lifecycle_actions import LifecycleActions
from app.gui.mode_status_bar import ModeStatusBar
from app.gui.open_filter_controller import OpenFilterController
from app.gui.page_view import PageView
from app.gui.reload_controller import ReloadController
from app.gui.save_controller import SaveController
from app.gui.window_geometry_controller import WindowGeometryController
from app.gui.working_document import WorkingDocument
from app.storage.backend import StorageBackend


def as_mock(obj: object) -> MagicMock:
    """Narrow a spec'd mock reached through a typed dataclass field back to MagicMock."""
    return cast("MagicMock", obj)


def make_lifecycle(source: Path | None = None) -> LifecycleActions:
    """Build a LifecycleActions whose fields are all spec'd mocks."""
    edit_bar = MagicMock(spec=EditBar)
    edit_bar.is_edit_mode.return_value = False
    save = MagicMock(spec=SaveController)
    save.confirm_unsaved.return_value = True
    return LifecycleActions(
        parent=MagicMock(spec=QWidget),
        save=save,
        open_filter=MagicMock(spec=OpenFilterController),
        doc_memories=MagicMock(spec=DocumentMemoryGroup),
        working_doc=MagicMock(spec=WorkingDocument),
        controller=MagicMock(spec=EditController),
        images=MagicMock(spec=ImageController),
        page_view=MagicMock(spec=PageView),
        bar=MagicMock(spec=OperationBar),
        mode_bar=MagicMock(spec=ModeStatusBar),
        edit_bar=edit_bar,
        recent=MagicMock(spec=RecentFilesStore),
        reload=MagicMock(spec=ReloadController),
        chrome=MagicMock(spec=ChromeController),
        geometry=MagicMock(spec=WindowGeometryController),
        backend=MagicMock(spec=StorageBackend),
        source=lambda: source,
        set_source=MagicMock(spec=lambda path: None),
        set_title=MagicMock(spec=lambda title: None),
    )


def test_open_pdf_rejects_unsupported_format(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shown: list[str] = []
    monkeypatch.setattr(
        confirm_dialog, "show_message", lambda parent, title, msg, *a, **k: shown.append(msg)
    )
    lc = make_lifecycle()
    lc.open_pdf(tmp_path / "doc.xyz")
    assert shown == [strings.MSG_UNSUPPORTED_FORMAT_FMT.format(name="doc.xyz")]
    as_mock(lc.working_doc.open).assert_not_called()
    as_mock(lc.set_source).assert_not_called()


def test_open_pdf_aborts_when_unsaved_not_confirmed(tmp_path: Path) -> None:
    lc = make_lifecycle()
    as_mock(lc.save.confirm_unsaved).return_value = False
    lc.open_pdf(tmp_path / "doc.pdf")
    as_mock(lc.doc_memories.capture).assert_not_called()
    as_mock(lc.working_doc.open).assert_not_called()
    as_mock(lc.set_source).assert_not_called()


def test_close_document_resets_view_state(tmp_path: Path) -> None:
    lc = make_lifecycle(source=tmp_path / "doc.pdf")
    lc.close_document()
    as_mock(lc.page_view.reset).assert_called_once_with()
    as_mock(lc.bar.update_for).assert_called_once_with(has_doc=False, is_pdf=False)
    as_mock(lc.mode_bar.set_dirty).assert_called_once_with(False)
    as_mock(lc.edit_bar.toggle_edit_mode).assert_not_called()
    as_mock(lc.reload.on_document_closed).assert_called_once_with()
    as_mock(lc.set_source).assert_called_once_with(None)
    as_mock(lc.set_title).assert_called_once_with(strings.WINDOW_TITLE)


def test_open_sibling_without_source_is_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    lc = make_lifecycle(source=None)
    lc.open_sibling(1)
    as_mock(lc.mode_bar.set_hint).assert_not_called()
    as_mock(lc.working_doc.open).assert_not_called()


def test_open_sibling_without_neighbor_sets_hint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(file_browser_model, "sibling_file", lambda *a: None)
    lc = make_lifecycle(source=tmp_path / "doc.pdf")
    lc.open_sibling(1)
    as_mock(lc.mode_bar.set_hint).assert_called_once_with(strings.HINT_NO_SIBLING_FILE)
    as_mock(lc.working_doc.open).assert_not_called()


def test_shutdown_blocked_by_unsaved_changes(tmp_path: Path) -> None:
    lc = make_lifecycle(source=tmp_path / "doc.pdf")
    as_mock(lc.save.confirm_unsaved).return_value = False
    assert lc.shutdown() is False
    as_mock(lc.chrome.save).assert_not_called()
    as_mock(lc.geometry.save).assert_not_called()
    as_mock(lc.backend.close).assert_not_called()


def test_shutdown_persists_and_closes(tmp_path: Path) -> None:
    source = tmp_path / "doc.pdf"
    lc = make_lifecycle(source=source)
    assert lc.shutdown() is True
    as_mock(lc.doc_memories.capture).assert_called_once_with(source)
    as_mock(lc.working_doc.close).assert_called_once_with()
    as_mock(lc.chrome.save).assert_called_once_with()
    as_mock(lc.geometry.save).assert_called_once_with()
    as_mock(lc.backend.close).assert_called_once_with()
