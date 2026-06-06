"""Round-trip and fallback behaviour for the field-outline settings store."""

from __future__ import annotations

from pathlib import Path

from app.config.outline_settings import (
    OutlineLineStyle,
    OutlineSettings,
    OutlineSettingsStore,
)


def test_defaults_when_file_absent(tmp_path: Path) -> None:
    store = OutlineSettingsStore(tmp_path / "outline.json")
    settings = store.load()
    assert settings == OutlineSettings()
    assert settings.width_px == 2
    assert settings.style is OutlineLineStyle.DASHED
    assert settings.color == "#FF0000"


def test_save_then_load_round_trip(tmp_path: Path) -> None:
    store = OutlineSettingsStore(tmp_path / "outline.json")
    saved = OutlineSettings(width_px=5, style=OutlineLineStyle.SOLID, color="#00FF00")
    store.save(saved)
    assert store.load() == saved


def test_unknown_style_falls_back_to_default(tmp_path: Path) -> None:
    path = tmp_path / "outline.json"
    store = OutlineSettingsStore(path)
    store.save(OutlineSettings(style=OutlineLineStyle.SOLID))
    # Corrupt the persisted style to an unknown value.
    text = path.read_text(encoding="utf-8").replace('"solid"', '"squiggly"')
    path.write_text(text, encoding="utf-8")
    assert store.load().style is OutlineSettings().style


def test_store_has_remembered_label(tmp_path: Path) -> None:
    store = OutlineSettingsStore(tmp_path / "outline.json")
    assert store.label == "Field outline appearance"
