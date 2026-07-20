"""Unit tests for the Open-with store and its palette actions."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QWidget

from app.config.open_with import OPEN_WITH_KEY, OPEN_WITH_VERSION, OpenWithStore
from app.gui import file_dialogs, open_with
from app.gui.filter_list_dialog import ListEntry
from app.gui.open_with import _ADD_FROM_FILE, _ADD_FROM_PROCESS, OpenWithActions
from app.gui.operations import OpResult
from app.gui.palette_controller import PaletteController
from app.os_integration import processes
from app.os_integration.processes import RunningApp
from app.storage.sqlite_backend import SqliteBackend

# --- store --------------------------------------------------------------------


def _store(tmp_path: Path) -> OpenWithStore:
    return OpenWithStore(SqliteBackend(tmp_path / "db.sqlite"))


def test_load_missing_returns_empty(tmp_path: Path) -> None:
    assert _store(tmp_path).load() == []


def test_add_then_load_round_trips(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.add(Path("/apps/Photoshop.exe"))
    store.add(Path("/apps/Gimp.exe"))
    # Append order preserved (a stable menu, not a recency list).
    assert store.load() == [Path("/apps/Photoshop.exe"), Path("/apps/Gimp.exe")]


def test_add_dedups(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.add(Path("/apps/a.exe"))
    store.add(Path("/apps/a.exe"))
    assert store.load() == [Path("/apps/a.exe")]


def test_remove_drops_entry(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.add(Path("/apps/a.exe"))
    store.add(Path("/apps/b.exe"))
    store.remove(Path("/apps/a.exe"))
    assert store.load() == [Path("/apps/b.exe")]


def test_remove_missing_is_noop(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.add(Path("/apps/a.exe"))
    store.remove(Path("/apps/nope.exe"))
    assert store.load() == [Path("/apps/a.exe")]


def test_corrupt_shape_degrades_to_empty(tmp_path: Path) -> None:
    backend = SqliteBackend(tmp_path / "db.sqlite")
    backend.set_versioned(OPEN_WITH_KEY, OPEN_WITH_VERSION, {"apps": "not-a-list"})
    assert OpenWithStore(backend).load() == []


# --- actions ------------------------------------------------------------------


def _fake_dialog(chosen: ListEntry | None) -> type:
    """A stand-in FilterListDialog: exec() truthy iff an entry is 'chosen'."""

    class _Fake:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def exec(self) -> bool:
            return chosen is not None

        def chosen(self) -> ListEntry | None:
            return chosen

    return _Fake


def _actions(
    *,
    store: object,
    source: object,
    report: object,
) -> OpenWithActions:
    return OpenWithActions(
        MagicMock(spec=QWidget),
        MagicMock(spec=PaletteController),
        store,  # type: ignore[arg-type]
        source,  # type: ignore[arg-type]
        report,  # type: ignore[arg-type]
    )


def test_entries_map_apps_and_append_two_add_rows(qapp: object) -> None:
    store = MagicMock(spec=OpenWithStore)
    store.load.return_value = [Path("C:/x/Photoshop.exe")]
    actions = _actions(store=store, source=lambda: Path("doc.pdf"), report=lambda r: None)
    entries = actions._entries()
    assert entries[0].title == "Photoshop"
    assert entries[0].payload == Path("C:/x/Photoshop.exe")
    assert entries[-2].payload is _ADD_FROM_FILE
    assert entries[-1].payload is _ADD_FROM_PROCESS


def test_launch_runs_app_with_source(
    qapp: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = tmp_path / "doc.pdf"
    src.write_bytes(b"%PDF-1.4")
    calls: list[list[str]] = []
    monkeypatch.setattr(subprocess, "Popen", lambda args: calls.append(args))
    reports: list[OpResult] = []
    actions = _actions(
        store=MagicMock(spec=OpenWithStore), source=lambda: src, report=reports.append
    )
    app = tmp_path / "editor.exe"
    actions._launch(app)
    assert calls == [[str(app), str(src)]]
    assert reports[-1].ok


def test_launch_reports_failure_on_oserror(
    qapp: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(_args: list[str]) -> None:
        raise OSError("no such app")

    monkeypatch.setattr(subprocess, "Popen", boom)
    reports: list[OpResult] = []
    src = tmp_path / "doc.pdf"
    src.write_bytes(b"%PDF-1.4")
    actions = _actions(
        store=MagicMock(spec=OpenWithStore), source=lambda: src, report=reports.append
    )
    actions._launch(tmp_path / "gone.exe")
    assert reports[-1].ok is False


def test_add_from_file_stores_browsed_exe(
    qapp: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = MagicMock(spec=OpenWithStore)
    picked = tmp_path / "Gimp.exe"
    monkeypatch.setattr(file_dialogs, "prompt_open_file", lambda *a, **k: picked)
    actions = _actions(store=store, source=lambda: Path("doc.pdf"), report=lambda r: None)
    assert actions._add_from_file() is True
    store.add.assert_called_once_with(picked)


def test_add_from_file_cancel_stores_nothing(qapp: object, monkeypatch: pytest.MonkeyPatch) -> None:
    store = MagicMock(spec=OpenWithStore)
    monkeypatch.setattr(file_dialogs, "prompt_open_file", lambda *a, **k: None)
    actions = _actions(store=store, source=lambda: Path("doc.pdf"), report=lambda r: None)
    assert actions._add_from_file() is False
    store.add.assert_not_called()


def test_add_from_process_stores_chosen_exe(qapp: object, monkeypatch: pytest.MonkeyPatch) -> None:
    store = MagicMock(spec=OpenWithStore)
    monkeypatch.setattr(
        processes,
        "running_apps",
        lambda: [RunningApp("Gimp", Path("C:/apps/Gimp.exe"))],
    )
    chosen = ListEntry(title="Gimp", payload=Path("C:/apps/Gimp.exe"))
    monkeypatch.setattr(open_with, "FilterListDialog", _fake_dialog(chosen))
    actions = _actions(store=store, source=lambda: Path("doc.pdf"), report=lambda r: None)
    assert actions._add_from_process() is True
    store.add.assert_called_once_with(Path("C:/apps/Gimp.exe"))


def test_add_from_process_cancel_stores_nothing(
    qapp: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = MagicMock(spec=OpenWithStore)
    monkeypatch.setattr(processes, "running_apps", lambda: [])
    monkeypatch.setattr(open_with, "FilterListDialog", _fake_dialog(None))
    actions = _actions(store=store, source=lambda: Path("doc.pdf"), report=lambda r: None)
    assert actions._add_from_process() is False
    store.add.assert_not_called()


def test_remove_calls_store_but_not_for_add_rows(qapp: object) -> None:
    store = MagicMock(spec=OpenWithStore)
    actions = _actions(store=store, source=lambda: Path("doc.pdf"), report=lambda r: None)
    actions._remove(ListEntry(title="Gimp", payload=Path("/apps/Gimp.exe")))
    store.remove.assert_called_once_with(Path("/apps/Gimp.exe"))
    actions._remove(ListEntry(title="from file", payload=_ADD_FROM_FILE))  # sentinel — ignored
    actions._remove(ListEntry(title="from proc", payload=_ADD_FROM_PROCESS))  # sentinel — ignored
    store.remove.assert_called_once()


def test_dispatch_file_row_reopens_after_adding(
    qapp: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    actions = _actions(
        store=MagicMock(spec=OpenWithStore), source=lambda: Path("doc.pdf"), report=lambda r: None
    )
    reopened: list[str] = []
    monkeypatch.setattr(actions, "_add_from_file", lambda: True)
    monkeypatch.setattr(actions, "show", lambda: reopened.append("show"))
    actions._dispatch(ListEntry(title="add", payload=_ADD_FROM_FILE))
    assert reopened == ["show"]


def test_dispatch_process_row_reopens_after_adding(
    qapp: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    actions = _actions(
        store=MagicMock(spec=OpenWithStore), source=lambda: Path("doc.pdf"), report=lambda r: None
    )
    reopened: list[str] = []
    monkeypatch.setattr(actions, "_add_from_process", lambda: True)
    monkeypatch.setattr(actions, "show", lambda: reopened.append("show"))
    actions._dispatch(ListEntry(title="add", payload=_ADD_FROM_PROCESS))
    assert reopened == ["show"]


def test_dispatch_app_row_launches(qapp: object, monkeypatch: pytest.MonkeyPatch) -> None:
    actions = _actions(
        store=MagicMock(spec=OpenWithStore), source=lambda: Path("doc.pdf"), report=lambda r: None
    )
    launched: list[Path] = []
    monkeypatch.setattr(actions, "_launch", lambda app: launched.append(app))
    actions._dispatch(ListEntry(title="Gimp", payload=Path("/apps/Gimp.exe")))
    assert launched == [Path("/apps/Gimp.exe")]


def test_show_without_document_opens_no_dialog(qapp: object) -> None:
    palette = MagicMock(spec=PaletteController)
    actions = OpenWithActions(
        MagicMock(spec=QWidget),
        palette,
        MagicMock(spec=OpenWithStore),
        lambda: None,  # no open document
        lambda r: None,
    )
    actions.show()
    palette.apply_to.assert_not_called()
