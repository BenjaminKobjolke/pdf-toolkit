"""Unit tests for the Remembered-settings reset flow (offscreen Qt)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from app.config.record_store import RecordStore
from app.gui.operations import OpResult
from app.gui.remembered_settings import RememberedSettingsController
from app.storage.sqlite_backend import SqliteBackend


def _store(backend: SqliteBackend, key: str, label: str) -> RecordStore:
    backend.set_versioned(key, 1, {"x": 1})
    store = RecordStore(backend, key)
    store.LABEL = label
    return store


def _patch_dialog(monkeypatch: pytest.MonkeyPatch, pick: int) -> None:
    """Replace FilterListDialog so it accepts and returns entry index ``pick``."""

    class FakeDialog:
        def __init__(self, entries: list[Any], *_args: Any, **_kw: Any) -> None:
            self._entries = entries

        def exec(self) -> bool:
            return True

        def chosen(self) -> Any:
            return self._entries[pick]

    monkeypatch.setattr("app.gui.remembered_settings.FilterListDialog", FakeDialog)


def test_reset_one_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    backend = SqliteBackend(tmp_path / "db.sqlite")
    a = _store(backend, "a", "A")
    b = _store(backend, "b", "B")
    _patch_dialog(monkeypatch, 0)  # first store
    reports: list[OpResult] = []
    RememberedSettingsController(None, [a, b], reports.append).open()
    assert backend.get_versioned("a", 1) is None
    assert backend.get_versioned("b", 1) is not None
    assert reports[0].ok


def test_clear_all(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    backend = SqliteBackend(tmp_path / "db.sqlite")
    a = _store(backend, "a", "A")
    b = _store(backend, "b", "B")
    _patch_dialog(monkeypatch, -1)  # the appended "clear all" entry
    reports: list[OpResult] = []
    RememberedSettingsController(None, [a, b], reports.append).open()
    assert backend.get_versioned("a", 1) is None
    assert backend.get_versioned("b", 1) is None
    assert reports[0].ok
