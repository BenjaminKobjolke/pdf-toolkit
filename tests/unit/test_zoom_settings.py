"""Round-trip, clamp, and fallback behaviour for the default-zoom store."""

from __future__ import annotations

from pathlib import Path

from app.config.zoom_settings import (
    ZOOM_PCT_MAX,
    ZOOM_PCT_MIN,
    ZoomSettings,
    ZoomSettingsStore,
)
from app.storage.sqlite_backend import SqliteBackend


def _store(tmp_path: Path) -> ZoomSettingsStore:
    return ZoomSettingsStore(SqliteBackend(tmp_path / "db.sqlite"))


def test_defaults_when_file_absent(tmp_path: Path) -> None:
    settings = _store(tmp_path).load()
    assert settings == ZoomSettings()
    assert settings.fit is True
    assert settings.percent == 100


def test_save_then_load_round_trip(tmp_path: Path) -> None:
    store = _store(tmp_path)
    saved = ZoomSettings(fit=False, percent=50)
    store.save(saved)
    assert store.load() == saved


def test_percent_clamped_to_bounds(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.save(ZoomSettings(fit=False, percent=ZOOM_PCT_MAX + 1000))
    assert store.load().percent == ZOOM_PCT_MAX
    store.save(ZoomSettings(fit=False, percent=1))
    assert store.load().percent == ZOOM_PCT_MIN


def test_store_has_remembered_label(tmp_path: Path) -> None:
    assert _store(tmp_path).label == "Default zoom"
