"""Unit tests for the persisted reload-on-changes default (ReloadSettingsStore)."""

from __future__ import annotations

from pathlib import Path

from app.config.reload_settings import ReloadSettings, ReloadSettingsStore
from tests.conftest import gui_backend


def test_default_is_off() -> None:
    assert ReloadSettings().watch_by_default is False


def test_defaults_when_absent(tmp_path: Path) -> None:
    store = ReloadSettingsStore(gui_backend(tmp_path))
    assert store.load() == ReloadSettings()


def test_round_trip(tmp_path: Path) -> None:
    backend = gui_backend(tmp_path)
    store = ReloadSettingsStore(backend)
    store.save(ReloadSettings(watch_by_default=True))
    assert ReloadSettingsStore(backend).load() == ReloadSettings(watch_by_default=True)


def test_reset_restores_defaults(tmp_path: Path) -> None:
    store = ReloadSettingsStore(gui_backend(tmp_path))
    store.save(ReloadSettings(watch_by_default=True))
    store.reset()
    assert store.load() == ReloadSettings()


def test_store_has_label() -> None:
    assert ReloadSettingsStore.LABEL
