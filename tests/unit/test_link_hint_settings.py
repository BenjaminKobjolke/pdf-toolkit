"""Unit tests for the link-overlay appearance store."""

from __future__ import annotations

from pathlib import Path

from app.config.link_hint_settings import (
    FONT_PT_MAX,
    FONT_PT_MIN,
    LINK_HINT_KEY,
    LINK_HINT_SETTINGS_VERSION,
    LinkHintSettings,
    LinkHintSettingsStore,
)
from tests.conftest import gui_backend


def test_defaults_when_absent(tmp_path: Path) -> None:
    store = LinkHintSettingsStore(gui_backend(tmp_path))
    assert store.load() == LinkHintSettings()


def test_round_trip_all_fields(tmp_path: Path) -> None:
    store = LinkHintSettingsStore(gui_backend(tmp_path))
    saved = LinkHintSettings(
        font_pt=20, text_color="#111111", background_color="#222222", box_color="#333333"
    )
    store.save(saved)
    assert store.load() == saved


def test_partial_row_fills_defaults(tmp_path: Path) -> None:
    backend = gui_backend(tmp_path)
    backend.set_versioned(LINK_HINT_KEY, LINK_HINT_SETTINGS_VERSION, {"font_pt": 30})
    loaded = LinkHintSettingsStore(backend).load()
    assert loaded.font_pt == 30
    assert loaded.text_color == LinkHintSettings().text_color
    assert loaded.box_color == LinkHintSettings().box_color


def test_font_bounds_sane() -> None:
    assert 1 <= FONT_PT_MIN < FONT_PT_MAX


def test_store_has_label(tmp_path: Path) -> None:
    assert LinkHintSettingsStore(gui_backend(tmp_path)).label
