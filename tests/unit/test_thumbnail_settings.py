"""Unit tests for the thumbnails-view size store."""

from __future__ import annotations

from pathlib import Path

from app.config.thumbnail_settings import (
    THUMB_KEY,
    THUMB_PX_MAX,
    THUMB_PX_MIN,
    THUMB_SETTINGS_VERSION,
    ThumbnailSettings,
    ThumbnailSettingsStore,
    clamp_thumb_size,
)
from tests.conftest import gui_backend


def test_defaults_when_absent(tmp_path: Path) -> None:
    store = ThumbnailSettingsStore(gui_backend(tmp_path))
    assert store.load() == ThumbnailSettings()


def test_default_size_is_256() -> None:
    assert ThumbnailSettings().size == 256


def test_round_trip(tmp_path: Path) -> None:
    store = ThumbnailSettingsStore(gui_backend(tmp_path))
    saved = ThumbnailSettings(size=512)
    store.save(saved)
    assert store.load() == saved


def test_stale_row_falls_back_to_default(tmp_path: Path) -> None:
    backend = gui_backend(tmp_path)
    backend.set_versioned(THUMB_KEY, THUMB_SETTINGS_VERSION, {"unrelated": True})
    assert ThumbnailSettingsStore(backend).load() == ThumbnailSettings()


def test_clamp_bounds() -> None:
    assert clamp_thumb_size(THUMB_PX_MIN - 1) == THUMB_PX_MIN
    assert clamp_thumb_size(THUMB_PX_MAX + 1) == THUMB_PX_MAX
    assert clamp_thumb_size(300) == 300


def test_bounds_sane() -> None:
    assert 1 <= THUMB_PX_MIN < ThumbnailSettings().size < THUMB_PX_MAX


def test_store_has_label(tmp_path: Path) -> None:
    assert ThumbnailSettingsStore(gui_backend(tmp_path)).label
