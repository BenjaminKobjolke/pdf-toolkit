"""Round-trip and fallback behaviour for the image-background settings store."""

from __future__ import annotations

from pathlib import Path

from app.config.image_background_settings import (
    IMAGE_BACKGROUND_KEY,
    IMAGE_BACKGROUND_SETTINGS_VERSION,
    ImageBackground,
    ImageBackgroundSettings,
    ImageBackgroundSettingsStore,
)
from app.storage.sqlite_backend import SqliteBackend


def _store(tmp_path: Path) -> ImageBackgroundSettingsStore:
    return ImageBackgroundSettingsStore(SqliteBackend(tmp_path / "db.sqlite"))


def test_defaults_when_absent(tmp_path: Path) -> None:
    settings = _store(tmp_path).load()
    assert settings == ImageBackgroundSettings()
    assert settings.background is ImageBackground.WHITE


def test_save_then_load_round_trip(tmp_path: Path) -> None:
    store = _store(tmp_path)
    saved = ImageBackgroundSettings(background=ImageBackground.CHECKER)
    store.save(saved)
    assert store.load() == saved


def test_unknown_background_falls_back_to_default(tmp_path: Path) -> None:
    # An unknown persisted value degrades to the default, not a crash.
    backend = SqliteBackend(tmp_path / "db.sqlite")
    backend.set_versioned(
        IMAGE_BACKGROUND_KEY,
        IMAGE_BACKGROUND_SETTINGS_VERSION,
        {"background": "plaid"},
    )
    store = ImageBackgroundSettingsStore(backend)
    assert store.load().background is ImageBackground.WHITE


def test_store_has_remembered_label(tmp_path: Path) -> None:
    assert _store(tmp_path).label == "Image transparency background"
