"""Unit tests for the text/markdown appearance store."""

from __future__ import annotations

from pathlib import Path

from app.config.text_view_settings import (
    FONT_PT_MAX,
    FONT_PT_MIN,
    TEXT_VIEW_KEY,
    TEXT_VIEW_SETTINGS_VERSION,
    TextViewSettings,
    TextViewSettingsStore,
)
from tests.conftest import gui_backend


def test_defaults_when_absent(tmp_path: Path) -> None:
    store = TextViewSettingsStore(gui_backend(tmp_path))
    assert store.load() == TextViewSettings()


def test_round_trip_all_fields(tmp_path: Path) -> None:
    store = TextViewSettingsStore(gui_backend(tmp_path))
    saved = TextViewSettings(font_pt=24, dark_mode=True)
    store.save(saved)
    assert store.load() == saved


def test_partial_row_fills_defaults(tmp_path: Path) -> None:
    backend = gui_backend(tmp_path)
    backend.set_versioned(TEXT_VIEW_KEY, TEXT_VIEW_SETTINGS_VERSION, {"dark_mode": True})
    loaded = TextViewSettingsStore(backend).load()
    assert loaded.dark_mode is True
    assert loaded.font_pt == TextViewSettings().font_pt


def test_font_bounds_sane() -> None:
    assert 1 <= FONT_PT_MIN < FONT_PT_MAX


def test_store_has_label(tmp_path: Path) -> None:
    assert TextViewSettingsStore(gui_backend(tmp_path)).label
