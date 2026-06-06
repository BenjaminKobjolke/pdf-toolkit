"""Unit tests for the Remembered-settings reset flow (offscreen Qt)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from app.config.file_backed_store import FileBackedStore
from app.gui.operations import OpResult
from app.gui.remembered_settings import RememberedSettingsController


def _store(path: Path, label: str) -> FileBackedStore:
    path.write_text("{}", encoding="utf-8")
    store = FileBackedStore(path)
    store.LABEL = label
    return store


def _patch_dialog(monkeypatch: pytest.MonkeyPatch, pick: int) -> None:
    """Replace FilterListDialog so it accepts and returns entry index ``pick``."""

    class FakeDialog:
        def __init__(self, entries: list[Any], **_kw: Any) -> None:
            self._entries = entries

        def exec(self) -> bool:
            return True

        def chosen(self) -> Any:
            return self._entries[pick]

    monkeypatch.setattr("app.gui.remembered_settings.FilterListDialog", FakeDialog)


def test_reset_one_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    a = _store(tmp_path / "a.json", "A")
    b = _store(tmp_path / "b.json", "B")
    _patch_dialog(monkeypatch, 0)  # first store
    reports: list[OpResult] = []
    RememberedSettingsController(None, [a, b], reports.append).open()
    assert not (tmp_path / "a.json").exists()
    assert (tmp_path / "b.json").exists()
    assert reports[0].ok


def test_clear_all(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    a = _store(tmp_path / "a.json", "A")
    b = _store(tmp_path / "b.json", "B")
    _patch_dialog(monkeypatch, -1)  # the appended "clear all" entry
    reports: list[OpResult] = []
    RememberedSettingsController(None, [a, b], reports.append).open()
    assert not (tmp_path / "a.json").exists()
    assert not (tmp_path / "b.json").exists()
    assert reports[0].ok
