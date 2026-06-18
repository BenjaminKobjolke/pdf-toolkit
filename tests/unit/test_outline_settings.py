"""Round-trip and fallback behaviour for the field-outline settings store."""

from __future__ import annotations

from pathlib import Path

from app.config.outline_settings import (
    OUTLINE_KEY,
    OUTLINE_SETTINGS_VERSION,
    OutlineLineStyle,
    OutlineSettings,
    OutlineSettingsStore,
)
from app.storage.sqlite_backend import SqliteBackend


def _store(tmp_path: Path) -> OutlineSettingsStore:
    return OutlineSettingsStore(SqliteBackend(tmp_path / "db.sqlite"))


def test_defaults_when_file_absent(tmp_path: Path) -> None:
    settings = _store(tmp_path).load()
    assert settings == OutlineSettings()
    assert settings.width_px == 2
    assert settings.style is OutlineLineStyle.DASHED
    assert settings.color == "#FF0000"


def test_save_then_load_round_trip(tmp_path: Path) -> None:
    store = _store(tmp_path)
    saved = OutlineSettings(width_px=5, style=OutlineLineStyle.SOLID, color="#00FF00")
    store.save(saved)
    assert store.load() == saved


def test_unknown_style_falls_back_to_default(tmp_path: Path) -> None:
    # An unknown persisted style degrades to the default, not a crash.
    backend = SqliteBackend(tmp_path / "db.sqlite")
    backend.set_versioned(
        OUTLINE_KEY,
        OUTLINE_SETTINGS_VERSION,
        {"width_px": 2, "style": "squiggly", "color": "#FF0000"},
    )
    assert OutlineSettingsStore(backend).load().style is OutlineSettings().style


def test_store_has_remembered_label(tmp_path: Path) -> None:
    assert _store(tmp_path).label == "Field outline appearance"
