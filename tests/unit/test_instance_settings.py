"""Unit tests for the single-instance (reuse window) settings store."""

from __future__ import annotations

from pathlib import Path

from app.config.instance_settings import InstanceSettings, InstanceSettingsStore
from tests.conftest import gui_backend


def test_default_is_reuse_window() -> None:
    assert InstanceSettings().reuse_window is True


def test_defaults_when_absent(tmp_path: Path) -> None:
    store = InstanceSettingsStore(gui_backend(tmp_path))
    assert store.load() == InstanceSettings()


def test_round_trip(tmp_path: Path) -> None:
    store = InstanceSettingsStore(gui_backend(tmp_path))
    store.save(InstanceSettings(reuse_window=False))
    assert store.load() == InstanceSettings(reuse_window=False)


def test_store_has_label(tmp_path: Path) -> None:
    assert InstanceSettingsStore(gui_backend(tmp_path)).label
