"""Unit tests for the last-placement-mode store (Qt-free, string-based)."""

from __future__ import annotations

from pathlib import Path

from app.config.placement_settings import PlacementStore
from app.storage.sqlite_backend import SqliteBackend


def _store(tmp_path: Path) -> PlacementStore:
    return PlacementStore(SqliteBackend(tmp_path / "db.sqlite"))


def test_load_missing_returns_none(tmp_path: Path) -> None:
    assert _store(tmp_path).load() is None


def test_save_then_load_round_trips(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.save("page_center")
    assert store.load() == "page_center"
