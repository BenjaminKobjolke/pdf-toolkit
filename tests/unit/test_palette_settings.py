"""Unit tests for persisted command-palette appearance settings."""

from __future__ import annotations

from pathlib import Path

from app.config.palette_settings import PaletteSettings, PaletteSettingsStore
from app.storage.sqlite_backend import SqliteBackend


def _store(tmp_path: Path) -> PaletteSettingsStore:
    return PaletteSettingsStore(SqliteBackend(tmp_path / "db.sqlite"))


def test_default_when_missing(tmp_path: Path) -> None:
    assert _store(tmp_path).load() == PaletteSettings()


def test_save_then_load_round_trips(tmp_path: Path) -> None:
    store = _store(tmp_path)
    settings = PaletteSettings(
        width_pct=50, height_pct=40, font_pt=14, borderless=True, opacity_pct=80
    )
    store.save(settings)
    assert store.load() == settings


def test_fields_persist_independently(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.save(PaletteSettings(width_pct=33, borderless=True))
    loaded = store.load()
    assert loaded.width_pct == 33
    assert loaded.borderless is True
    assert loaded.height_pct == PaletteSettings().height_pct
