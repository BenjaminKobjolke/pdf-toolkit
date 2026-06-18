"""Unit tests for persisted UI state."""

from __future__ import annotations

from pathlib import Path

from app.config.ui_state import UiState, UiStateStore
from app.storage.sqlite_backend import SqliteBackend


def _store(tmp_path: Path) -> UiStateStore:
    return UiStateStore(SqliteBackend(tmp_path / "db.sqlite"))


def test_default_when_missing(tmp_path: Path) -> None:
    state = _store(tmp_path).load()
    # Status bar defaults to visible; menu/toolbar hidden.
    assert state == UiState(menu_visible=False, toolbar_visible=False, statusbar_visible=True)


def test_save_then_load_round_trips(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.save(UiState(menu_visible=True, toolbar_visible=True, statusbar_visible=False))
    assert store.load() == UiState(menu_visible=True, toolbar_visible=True, statusbar_visible=False)


def test_fields_persist_independently(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.save(UiState(menu_visible=False, toolbar_visible=True, statusbar_visible=False))
    assert store.load() == UiState(
        menu_visible=False, toolbar_visible=True, statusbar_visible=False
    )
