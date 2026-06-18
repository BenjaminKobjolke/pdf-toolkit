"""Unit tests for the window-geometry store."""

from __future__ import annotations

from pathlib import Path

from app.config.window_geometry import (
    WINDOW_GEOMETRY_KEY,
    WINDOW_GEOMETRY_VERSION,
    WindowGeometry,
    WindowGeometryStore,
)
from app.storage.sqlite_backend import SqliteBackend


def _store(tmp_path: Path) -> WindowGeometryStore:
    return WindowGeometryStore(SqliteBackend(tmp_path / "db.sqlite"))


def test_load_missing_returns_none(tmp_path: Path) -> None:
    assert _store(tmp_path).load() is None


def test_save_then_load_round_trips(tmp_path: Path) -> None:
    store = _store(tmp_path)
    geom = WindowGeometry(x=10, y=20, width=640, height=480)
    store.save(geom)
    assert store.load() == geom


def test_load_incomplete_returns_none(tmp_path: Path) -> None:
    # A stored object missing required keys degrades to None, not a crash.
    backend = SqliteBackend(tmp_path / "db.sqlite")
    backend.set_versioned(WINDOW_GEOMETRY_KEY, WINDOW_GEOMETRY_VERSION, {"x": 1, "y": 2})
    assert WindowGeometryStore(backend).load() is None
