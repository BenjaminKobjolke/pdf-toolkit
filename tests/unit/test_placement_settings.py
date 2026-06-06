"""Unit tests for the last-placement-mode store (Qt-free, string-based)."""

from __future__ import annotations

from pathlib import Path

from app.config.placement_settings import PlacementStore


def _store(tmp_path: Path) -> PlacementStore:
    return PlacementStore(tmp_path / "nested" / "placement.json")


def test_load_missing_returns_none(tmp_path: Path) -> None:
    assert _store(tmp_path).load() is None


def test_save_then_load_round_trips(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.save("page_center")
    assert store.load() == "page_center"


def test_load_corrupt_returns_none(tmp_path: Path) -> None:
    path = tmp_path / "placement.json"
    path.write_text("{ not json", encoding="utf-8")
    assert PlacementStore(path).load() is None
