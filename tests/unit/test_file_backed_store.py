"""Unit tests for the FileBackedStore base."""

from __future__ import annotations

from pathlib import Path

from app.config.file_backed_store import FileBackedStore


def test_reset_deletes_file(tmp_path: Path) -> None:
    path = tmp_path / "x.json"
    path.write_text("{}", encoding="utf-8")
    store = FileBackedStore(path)
    assert store.path == path
    store.reset()
    assert not path.exists()


def test_reset_absent_is_noop(tmp_path: Path) -> None:
    FileBackedStore(tmp_path / "missing.json").reset()  # must not raise


def test_label_default() -> None:
    assert FileBackedStore(Path("x")).label == "setting"


def test_subclass_label() -> None:
    class Demo(FileBackedStore):
        LABEL = "Demo setting"

    assert Demo(Path("x")).label == "Demo setting"
