"""Unit tests for the command-usage history store and ordering helper."""

from __future__ import annotations

from pathlib import Path

from app.config.command_history import MAX_HISTORY, CommandHistoryStore, order_ids
from app.storage.sqlite_backend import SqliteBackend


def _store(tmp_path: Path) -> CommandHistoryStore:
    return CommandHistoryStore(SqliteBackend(tmp_path / "db.sqlite"))


def test_load_missing_returns_empty(tmp_path: Path) -> None:
    assert _store(tmp_path).load() == []


def test_add_then_load_round_trips(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.add("open")
    store.add("save")
    assert store.load() == ["save", "open"]


def test_add_dedups_and_moves_to_front(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.add("open")
    store.add("save")
    store.add("open")
    assert store.load() == ["open", "save"]


def test_add_caps_at_max(tmp_path: Path) -> None:
    store = _store(tmp_path)
    for i in range(MAX_HISTORY + 10):
        store.add(f"cmd{i}")
    loaded = store.load()
    assert len(loaded) == MAX_HISTORY
    assert loaded[0] == f"cmd{MAX_HISTORY + 9}"


def test_order_ids_floats_mru_first() -> None:
    all_ids = ["a", "b", "c", "d"]
    assert order_ids(all_ids, ["c", "a"]) == ["c", "a", "b", "d"]


def test_order_ids_ignores_unknown_mru() -> None:
    all_ids = ["a", "b"]
    assert order_ids(all_ids, ["x", "b"]) == ["b", "a"]


def test_order_ids_empty_mru_keeps_order() -> None:
    all_ids = ["a", "b", "c"]
    assert order_ids(all_ids, []) == ["a", "b", "c"]
