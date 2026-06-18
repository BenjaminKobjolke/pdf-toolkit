"""Unit tests for the RecordStore base."""

from __future__ import annotations

from pathlib import Path

from app.config.record_store import RecordStore
from app.storage.sqlite_backend import SqliteBackend


def _backend(tmp_path: Path) -> SqliteBackend:
    return SqliteBackend(tmp_path / "db.sqlite")


def test_reset_deletes_row(tmp_path: Path) -> None:
    backend = _backend(tmp_path)
    backend.set_versioned("demo", 1, {"a": 1})
    store = RecordStore(backend, "demo")
    store.reset()
    assert backend.get_versioned("demo", 1) is None


def test_reset_absent_is_noop(tmp_path: Path) -> None:
    RecordStore(_backend(tmp_path), "missing").reset()  # must not raise


def test_label_default(tmp_path: Path) -> None:
    assert RecordStore(_backend(tmp_path), "x").label == "setting"


def test_subclass_label(tmp_path: Path) -> None:
    class Demo(RecordStore):
        LABEL = "Demo setting"

    assert Demo(_backend(tmp_path), "x").label == "Demo setting"
