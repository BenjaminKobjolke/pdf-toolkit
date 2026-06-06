"""Unit tests for the window-geometry store."""

from __future__ import annotations

from pathlib import Path

from app.config.window_geometry import WindowGeometry, WindowGeometryStore


def _store(tmp_path: Path) -> WindowGeometryStore:
    return WindowGeometryStore(tmp_path / "nested" / "window.json")


def test_load_missing_returns_none(tmp_path: Path) -> None:
    assert _store(tmp_path).load() is None


def test_save_then_load_round_trips(tmp_path: Path) -> None:
    store = _store(tmp_path)
    geom = WindowGeometry(x=10, y=20, width=640, height=480)
    store.save(geom)
    assert store.load() == geom


def test_load_corrupt_returns_none(tmp_path: Path) -> None:
    path = tmp_path / "window.json"
    path.write_text("{ not json", encoding="utf-8")
    assert WindowGeometryStore(path).load() is None


def test_load_incomplete_returns_none(tmp_path: Path) -> None:
    store = WindowGeometryStore(tmp_path / "window.json")
    # A versioned dict missing required keys degrades to None, not a crash.
    from app.io.json_store import write_versioned

    write_versioned(tmp_path / "window.json", 1, {"x": 1, "y": 2})
    assert store.load() is None
