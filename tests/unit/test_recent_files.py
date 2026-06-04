"""Unit tests for the recent-documents store."""

from __future__ import annotations

from pathlib import Path

from app.config.recent_files import MAX_RECENT, RecentFilesStore


def _store(tmp_path: Path) -> RecentFilesStore:
    return RecentFilesStore(tmp_path / "nested" / "recent.json")


def test_load_missing_returns_empty(tmp_path: Path) -> None:
    assert _store(tmp_path).load() == []


def test_add_then_load_round_trips(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.add(Path("/docs/a.pdf"))
    store.add(Path("/docs/b.pdf"))
    # Most-recent first.
    assert store.load() == [Path("/docs/b.pdf"), Path("/docs/a.pdf")]


def test_add_dedups_and_moves_to_front(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.add(Path("/docs/a.pdf"))
    store.add(Path("/docs/b.pdf"))
    store.add(Path("/docs/a.pdf"))
    assert store.load() == [Path("/docs/a.pdf"), Path("/docs/b.pdf")]


def test_add_caps_at_max(tmp_path: Path) -> None:
    store = _store(tmp_path)
    for i in range(MAX_RECENT + 10):
        store.add(Path(f"/docs/f{i}.pdf"))
    loaded = store.load()
    assert len(loaded) == MAX_RECENT
    assert loaded[0] == Path(f"/docs/f{MAX_RECENT + 9}.pdf")


def test_clear_empties_store(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.add(Path("/docs/a.pdf"))
    store.clear()
    assert store.load() == []


def test_load_corrupt_returns_empty(tmp_path: Path) -> None:
    path = tmp_path / "recent.json"
    path.write_text("{ not json", encoding="utf-8")
    assert RecentFilesStore(path).load() == []
